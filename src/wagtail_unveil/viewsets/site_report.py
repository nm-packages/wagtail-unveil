from django.conf import settings
from django.urls import NoReverseMatch, reverse
from wagtail.models import Site

from wagtail_unveil.models import UrlEntry
from wagtail_unveil.viewsets.base import UnveilReportView, UnveilReportViewSet


def get_site_urls(base_url, max_instances):
    # Return a list of tuples (model_name, url_type, full_url) for sites
    urls = []
    
    # Add index and add URLs
    try:
        index_url = reverse('wagtailsites:index')
        urls.append(('wagtail.Site', 'index', f"{base_url}{index_url}"))
    except NoReverseMatch:
        pass
    try:
        add_url = reverse('wagtailsites:add')
        urls.append(('wagtail.Site', 'add', f"{base_url}{add_url}"))
    except NoReverseMatch:
        pass
    try:
        sites = Site.objects.all()[:max_instances] if max_instances else Site.objects.all()
        for site in sites:
            site_model_name = f"wagtail.Site ({site.hostname})"
            # Admin URLs
            try:
                edit_url = reverse('wagtailsites:edit', args=[site.id])
                urls.append((site_model_name, 'edit', f"{base_url}{edit_url}"))
            except NoReverseMatch:
                pass
            try:
                delete_url = reverse('wagtailsites:delete', args=[site.id])
                urls.append((site_model_name, 'delete', f"{base_url}{delete_url}"))
            except NoReverseMatch:
                pass
            # Frontend URL (actual site URL)
            # Left here but commented out because it may not be needed
            # this should be handled by the Page Report
            # protocol = "https" if site.port == 443 else "http"
            # if site.port in [80, 443]:
            #     frontend_url = f"{protocol}://{site.hostname}/"
            # else:
            #     frontend_url = f"{protocol}://{site.hostname}:{site.port}/"
            # if frontend_url:
            #     urls.append((site_model_name, 'frontend', frontend_url))
    except Site.DoesNotExist:
        pass
    except (AttributeError, ValueError, TypeError):
        pass
    return urls


class UnveilSiteReportIndexView(UnveilReportView):
    # Index view for the Site Report
    api_slug = "site"
    template_name = "wagtail_unveil/unveil_url_report.html"
    results_template_name = "wagtail_unveil/unveil_url_report_results.html"
    page_title = "Unveil Site"
    header_icon = "home"
    paginate_by = None

    def get_queryset(self):
        # Get the queryset for site URLs
        all_urls = []
        counter = 1
        max_instances = getattr(settings, "WAGTAIL_UNVEIL_MAX_INSTANCES", 1)
        base_url = getattr(settings, "WAGTAIL_UNVEIL_BASE_URL", "http://localhost:8000")
        site_urls = get_site_urls(base_url, max_instances)
        for model_name, url_type, url in site_urls:
            all_urls.append(UrlEntry(counter, model_name, url_type, url))
            counter += 1
            
        return all_urls


class UnveilSiteReportViewSet(UnveilReportViewSet):
    # ViewSet for Unveil Site reports
    icon = "home"
    menu_label = "Site"
    menu_name = "unveil_site_report"
    url_namespace = "unveil_site_report"
    url_prefix = "unveil/site-report"
    index_view_class = UnveilSiteReportIndexView
    



# Create an instance of the ViewSet to be registered
unveil_site_viewset = UnveilSiteReportViewSet("unveil_site_report")
