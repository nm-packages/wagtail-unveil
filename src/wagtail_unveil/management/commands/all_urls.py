from typing import Dict, List, Tuple, Any, Optional
from django.core.management.base import BaseCommand
from django.urls import URLPattern, URLResolver, get_resolver


class Command(BaseCommand):
    help = "Lists all admin URLs in the project"

    # Constants
    ADMIN_FILTER = "admin"
    WAGTAIL_ADMIN_KEY = "admin"
    WAGTAIL_ADMIN_DISPLAY = "wagtail-admin"
    OTHER_ADMIN_KEY = "other-admin"
    ALL_GROUPS_OPTION = "All groups"
    
    # Styling constants
    SECTION_MARKER = "▶"
    SEPARATOR_DOT = "•"

    def handle(self, *args: Any, **options: Any) -> None:
        """Main entry point for the command."""
        resolver = get_resolver()
        all_urls = self._collect_urls(resolver.url_patterns)
        admin_groups = self._filter_and_group_admin_urls(all_urls)
        
        if not admin_groups:
            self.stdout.write(self.style.WARNING("No admin URLs found in the project."))
            return
        
        selected_groups = self._get_user_selection(admin_groups)
        self._display_urls(selected_groups)

    def _collect_urls(self, patterns: List[Any], parent_path: str = '') -> List[Dict[str, str]]:
        """Recursively collect all URL patterns."""
        urls = []
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                pattern_path = parent_path + str(pattern.pattern)
                urls.append({
                    'path': pattern_path,
                    'name': pattern.name,
                    'callback': f"{pattern.callback.__module__}.{pattern.callback.__name__}"
                })
            elif isinstance(pattern, URLResolver):
                resolver_path = parent_path + str(pattern.pattern)
                urls.extend(self._collect_urls(pattern.url_patterns, resolver_path))
        return urls

    def _filter_and_group_admin_urls(self, all_urls: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Filter URLs containing 'admin' and group them by prefix."""
        admin_groups = {}
        
        for url in all_urls:
            path = url['path']
            if self.ADMIN_FILTER in path.lower():
                group_key = self._get_group_key(path)
                
                if group_key not in admin_groups:
                    admin_groups[group_key] = []
                admin_groups[group_key].append(url)
        
        return admin_groups

    def _get_group_key(self, path: str) -> str:
        """Determine the group key for a given URL path."""
        path_parts = path.strip('^').split('/')
        if not path_parts:
            return self.OTHER_ADMIN_KEY
            
        first_part = path_parts[0]
        if self.ADMIN_FILTER in first_part.lower():
            return first_part
        
        # Look for admin in subsequent parts
        for part in path_parts:
            if self.ADMIN_FILTER in part.lower():
                return part
        
        return self.OTHER_ADMIN_KEY

    def _get_display_name(self, group_name: str) -> str:
        """Get the display name for a group."""
        return self.WAGTAIL_ADMIN_DISPLAY if group_name == self.WAGTAIL_ADMIN_KEY else group_name

    def _get_user_selection(self, admin_groups: Dict[str, List[Dict[str, str]]]) -> List[Tuple[str, List[Dict[str, str]]]]:
        """Display menu and get user's group selection."""
        self._display_group_menu(admin_groups)
        
        group_list = sorted(admin_groups.keys())
        max_choice = len(group_list) + 1
        
        while True:
            try:
                choice = input(f"\nEnter your choice (1-{max_choice}): ").strip()
                choice_num = int(choice)
                
                if choice_num == max_choice:
                    return list(admin_groups.items())
                elif 1 <= choice_num <= len(group_list):
                    selected_group = group_list[choice_num - 1]
                    return [(selected_group, admin_groups[selected_group])]
                else:
                    self.stdout.write(self.style.ERROR(f"Please enter a number between 1 and {max_choice}"))
                    
            except ValueError:
                self.stdout.write(self.style.ERROR("Please enter a valid number"))
            except (KeyboardInterrupt, EOFError):
                self.stdout.write(self.style.ERROR("\nOperation cancelled."))
                return []

    def _display_group_menu(self, admin_groups: Dict[str, List[Dict[str, str]]]) -> None:
        """Display the available admin URL groups menu."""
        self.stdout.write(self.style.SUCCESS("\nAvailable admin URL groups:"))
        
        group_list = sorted(admin_groups.keys())
        for i, group_name in enumerate(group_list, 1):
            count = len(admin_groups[group_name])
            display_name = self._get_display_name(group_name)
            self.stdout.write(f"{i}. {display_name} ({count} URLs)")
        
        self.stdout.write(f"{len(group_list) + 1}. {self.ALL_GROUPS_OPTION}")

    def _display_urls(self, selected_groups: List[Tuple[str, List[Dict[str, str]]]]) -> None:
        """Display the selected URL groups with formatting."""
        if not selected_groups:
            return
            
        for group_name, urls in selected_groups:
            self._display_group_section(group_name, urls)

    def _display_group_section(self, group_name: str, urls: List[Dict[str, str]]) -> None:
        """Display a single group section with its URLs."""
        display_name = self._get_display_name(group_name)
        self.stdout.write(self.style.SUCCESS(f"\n=== {display_name.upper()} URLs ==="))
        self.stdout.write(f"Found {len(urls)} URLs in this group\n")
        self.stdout.write("")  # Extra line for spacing
        
        sorted_urls = sorted(urls, key=lambda x: x['path'])
        current_prefix = None
        
        for url in sorted_urls:
            current_prefix = self._display_url_with_grouping(url, current_prefix)
        
        self.stdout.write('')  # Extra line between groups

    def _display_url_with_grouping(self, url: Dict[str, str], current_prefix: Optional[str]) -> Optional[str]:
        """Display a single URL with grouping markers if needed."""
        path_parts = url['path'].strip('^').split('/')
        meaningful_parts = [part for part in path_parts if part]
        
        # Add grouping marker for URLs with multiple parts
        if len(meaningful_parts) >= 2:
            prefix = '/'.join(meaningful_parts[:2])
            
            if prefix != current_prefix:
                if current_prefix is not None:
                    self.stdout.write('')  # Extra line between prefix groups
                self.stdout.write(self.style.HTTP_INFO(f"{self.SECTION_MARKER} {prefix}/..."))
                current_prefix = prefix
        
        # Style and display the URL
        styled_path = self._get_styled_path(url['path'])
        faded_dot = self.style.HTTP_NOT_MODIFIED(self.SEPARATOR_DOT)
        
        self.stdout.write(
            f"Path: {styled_path} {faded_dot} Name: {url['name']} {faded_dot} View: {url['callback']}"
        )
        
        return current_prefix

    def _get_styled_path(self, path: str) -> str:
        """Apply appropriate styling to URL path based on whether it has dynamic parts."""
        if self._has_dynamic_parts(path):
            return self.style.WARNING(path)
        else:
            return self.style.SUCCESS(path)

    def _has_dynamic_parts(self, path: str) -> bool:
        """Check if URL path contains dynamic parts."""
        return ('<' in path and '>' in path) or ('(' in path and ')' in path)
