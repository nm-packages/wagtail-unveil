from django.conf import settings
from django.urls import NoReverseMatch, reverse
from wagtail.contrib.forms.models import FormSubmission
from wagtail.models import Page

from wagtail_unveil.models import UrlEntry
from wagtail_unveil.viewsets.base import UnveilReportView, UnveilReportViewSet


def get_form_pages_with_submissions():
    # Get all pages that have form submissions
    form_pages = []
    
    # Get unique page IDs that have form submissions
    try:
        page_ids_with_submissions = FormSubmission.objects.values_list('page_id', flat=True).distinct()
    except (FormSubmission.DoesNotExist, AttributeError, ValueError, TypeError):
        return form_pages
    
    for page_id in page_ids_with_submissions:
        try:
            page = Page.objects.get(id=page_id)
            specific_page = page.specific
            submission_count = FormSubmission.objects.filter(page_id=page_id).count()
            form_pages.append((
                page_id,
                page.title,
                specific_page.__class__.__name__,
                submission_count
            ))
        except Page.DoesNotExist:
            continue
        except (AttributeError, ValueError, TypeError):
            continue
    
    return form_pages


def get_forms_urls(base_url, max_instances):
    # Return a list of tuples (model_name, url_type, url) for forms
    urls = []
    
    # Get the FormSubmission model name
    form_submission_model_name = f"{FormSubmission._meta.app_label}.{FormSubmission.__name__}"

    # Get forms index URL
    try:
        forms_index_url = reverse('wagtailforms:index')
        urls.append((form_submission_model_name, "forms_index", f"{base_url}{forms_index_url}"))
    except NoReverseMatch:
        pass

    # Get form pages with submissions
    form_pages = get_form_pages_with_submissions()

    # Limit the number of form pages processed
    if max_instances:
        limited_form_pages = form_pages[:max_instances]
    else:
        limited_form_pages = form_pages

    for page_id, page_title, page_class_name, submission_count in limited_form_pages:
        # Create a model identifier that includes the page info
        form_page_model_name = f"{form_submission_model_name} ({page_title})"

        # Get submissions list URL
        try:
            list_url = reverse('wagtailforms:list_submissions', args=[page_id])
            urls.append((form_page_model_name, "list_submissions", f"{base_url}{list_url}"))
        except NoReverseMatch:
            pass

        # Get submissions delete URL
        try:
            delete_url = reverse('wagtailforms:delete_submissions', args=[page_id])
            urls.append((form_page_model_name, "delete_submissions", f"{base_url}{delete_url}"))
        except NoReverseMatch:
            pass

        # Also add the frontend form URL if available
        try:
            page = Page.objects.get(id=page_id)
            frontend_url = page.url
            if frontend_url:
                urls.append((form_page_model_name, "frontend_form", f"{base_url.rstrip('/')}" + frontend_url))
        except (Page.DoesNotExist, AttributeError, ValueError, TypeError):
            pass

    return urls


class UnveilFormReportIndexView(UnveilReportView):
    # Index view for the Form Report
    api_slug = "form"
    template_name = "wagtail_unveil/unveil_url_report.html"
    results_template_name = "wagtail_unveil/unveil_url_report_results.html"
    page_title = "Unveil Form "
    header_icon = "form"
    paginate_by = None

    def get_queryset(self):
        all_urls = []
        counter = 1
        max_instances = getattr(settings, "WAGTAIL_UNVEIL_MAX_INSTANCES", 1)
        base_url = getattr(settings, "WAGTAIL_UNVEIL_BASE_URL", "http://localhost:8000")
        form_urls = get_forms_urls(base_url, max_instances)
        for model_name, url_type, url in form_urls:
            all_urls.append(UrlEntry(counter, model_name, url_type, url))
            counter += 1
        return all_urls

class UnveilFormReportViewSet(UnveilReportViewSet):
    # ViewSet for Unveil Form reports
    model = None
    icon = "form"
    menu_label = "Form"
    menu_name = "unveil_form_report"
    url_namespace = "unveil_form_report"
    url_prefix = "unveil/form-report"
    index_view_class = UnveilFormReportIndexView



unveil_form_viewset = UnveilFormReportViewSet("unveil_form_report")
