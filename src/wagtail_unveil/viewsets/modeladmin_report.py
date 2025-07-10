from django.apps import apps
from django.conf import settings
from django.urls import NoReverseMatch, reverse

from wagtail_unveil.models import UrlEntry
from wagtail_unveil.viewsets.base import UnveilReportView, UnveilReportViewSet


def get_modeladmin_models():
    # Get all models for the modeladmin report
    # Get the list of models from settings
    modeladmin_models_list = getattr(settings, 'WAGTAIL_UNVEIL_WAGTAIL_MODELADMIN_MODELS', [])
    
    models = []
    for model_path in modeladmin_models_list:
        try:
            app_label, model_name = model_path.rsplit('.', 1)
            model = apps.get_model(app_label, model_name)
            models.append(model)
        except (LookupError, ValueError):
            continue
    
    return models


def get_modeladmin_url_patterns(model):
    """
    Get the URL pattern prefix for a ModelAdmin model.
    
    Wagtail ModelAdmin can use either:
    1. Default pattern: {app_label}_{model_name}_modeladmin_{action}
    2. Custom pattern: {base_url_path}_modeladmin_{action} (when base_url_path is set)
    
    Since we can't easily access the ModelAdmin registry, we'll try to detect
    which pattern is used by attempting to reverse a known URL.
    """
    app_label = model._meta.app_label
    model_name_lower = model._meta.model_name
    
    # Try the default pattern first
    default_pattern = f"{app_label}_{model_name_lower}_modeladmin_index"
    try:
        reverse(default_pattern)
        return f"{app_label}_{model_name_lower}_modeladmin"
    except NoReverseMatch:
        pass
    
    # If default pattern fails, try to find a custom base_url_path pattern
    # We'll look for any pattern that ends with "_modeladmin_index" for this model
    from django.urls import get_resolver
    resolver = get_resolver()
    
    def find_modeladmin_patterns(patterns, namespace=''):
        found_patterns = []
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):
                found_patterns.extend(find_modeladmin_patterns(pattern.url_patterns, namespace))
            else:
                if hasattr(pattern, 'name') and pattern.name:
                    if pattern.name.endswith('_modeladmin_index'):
                        # Check if this pattern works by trying to reverse it
                        try:
                            reverse(pattern.name)
                            # Extract the base pattern (remove _index)
                            base_pattern = pattern.name.replace('_index', '')
                            found_patterns.append(base_pattern)
                        except NoReverseMatch:
                            pass
        return found_patterns
    
    modeladmin_patterns = find_modeladmin_patterns(resolver.url_patterns)
    
    # Return the first pattern that works, or None if none found
    if modeladmin_patterns:
        return modeladmin_patterns[0]
    
    return None


def get_modeladmin_urls(base_url, max_instances):
    # Return a list of tuples (model_name, url_type, url) for modeladmin models
    urls = []
    modeladmin_models = get_modeladmin_models()
    for model in modeladmin_models:
        model_name = f"{model._meta.app_label}.{model.__name__}"
        
        # Get the URL pattern prefix for this model
        url_pattern_prefix = get_modeladmin_url_patterns(model)
        if not url_pattern_prefix:
            continue  # Skip if we can't find the URL pattern
        
        # Add URL
        try:
            add_url = reverse(f"{url_pattern_prefix}_create")
            urls.append((model_name, "add", f"{base_url}{add_url}"))
        except NoReverseMatch:
            pass
        
        # List URL
        try:
            list_url = reverse(f"{url_pattern_prefix}_index")
            urls.append((model_name, "list", f"{base_url}{list_url}"))
        except NoReverseMatch:
            pass
        
        # Instances
        try:
            instances = model.objects.all()
            if max_instances:
                instances = instances[:max_instances]
        except (model.DoesNotExist, AttributeError, ValueError, TypeError):
            continue
        
        for instance in instances:
            # Edit URL
            try:
                edit_url = reverse(f"{url_pattern_prefix}_edit", args=[instance.pk])
                urls.append((model_name, "edit", f"{base_url}{edit_url}"))
            except NoReverseMatch:
                pass
            
            # Delete URL
            try:
                delete_url = reverse(f"{url_pattern_prefix}_delete", args=[instance.pk])
                urls.append((model_name, "delete", f"{base_url}{delete_url}"))
            except NoReverseMatch:
                pass
            
            # History URL
            try:
                history_url = reverse(f"{url_pattern_prefix}_history", args=[instance.pk])
                urls.append((model_name, "history", f"{base_url}{history_url}"))
            except NoReverseMatch:
                pass
    
    return urls


class UnveilModelAdminReportIndexView(UnveilReportView):
    # Index view for the ModelAdmin Report
    api_slug = "modeladmin"
    template_name = "wagtail_unveil/unveil_url_report.html"
    results_template_name = "wagtail_unveil/unveil_url_report_results.html"
    page_title = "Unveil Wagtail ModelAdmin "
    header_icon = "code"
    paginate_by = None

    def get_queryset(self):
        all_urls = []
        counter = 1
        max_instances = getattr(settings, "WAGTAIL_UNVEIL_MAX_INSTANCES", 1)
        base_url = getattr(settings, "WAGTAIL_UNVEIL_BASE_URL", "http://localhost:8000")
        modeladmin_urls = get_modeladmin_urls(base_url, max_instances)
        for model_name, url_type, url in modeladmin_urls:
            all_urls.append(UrlEntry(counter, model_name, url_type, url))
            counter += 1
        return all_urls


class UnveilModelAdminReportViewSet(UnveilReportViewSet):
    # ViewSet for Unveil Wagtail ModelAdmin reports
    model = None
    icon = "code"
    menu_label = "Wagtail ModelAdmin"
    menu_name = "unveil_modeladmin_report"
    url_namespace = "unveil_modeladmin_report"
    url_prefix = "unveil/modeladmin-report"
    index_view_class = UnveilModelAdminReportIndexView


unveil_modeladmin_viewset = UnveilModelAdminReportViewSet("unveil_modeladmin_report")
