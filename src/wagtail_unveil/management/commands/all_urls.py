from django.core.management.base import BaseCommand
from django.urls import URLPattern, URLResolver, get_resolver


class Command(BaseCommand):
    help = """
    Lists all admin URLs in the project
    
    Used to identify and display all admin-related URLs in a Django project so 
    that developers can easily identify them.
    """

    # Constants
    ADMIN_FILTER = "admin"
    WAGTAIL_ADMIN_KEY = "admin"
    WAGTAIL_ADMIN_DISPLAY = "wagtail-admin"
    OTHER_ADMIN_KEY = "other-admin"
    ALL_GROUPS_OPTION = "All groups"
    
    # Styling constants
    SECTION_MARKER = "▶"
    SEPARATOR_DOT = "•"

    # File output name
    OUTPUT_FILE_NAME = "all_urls.txt" # Add this ito .gitignore to avoid committing the output file

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--static',
            action='store_true',
            help="Display only URLs with static parts",
        )
        parser.add_argument(
            '--dynamic',
            action='store_true',
            help="Display only URLs with dynamic parts",
        )
        parser.add_argument(
            '--tofile',
            action='store_true',
            help="Write the output to a file instead of printing to console",
        )

    def handle(self, *args, **options):
        """Main entry point for the command."""
        resolver = get_resolver()
        all_urls = self._collect_urls(resolver.url_patterns)
        admin_groups = self._filter_and_group_admin_urls(all_urls, options)
        
        if not admin_groups:
            self.stdout.write(self.style.WARNING("No admin URLs found in the project."))
            return
        
        selected_groups = self._get_user_selection(admin_groups)
        self._display_urls(selected_groups, options)

    def _collect_urls(self, patterns, parent_path=''):
        """Recursively collect all URL patterns."""
        urls = []
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                pattern_path = parent_path + str(pattern.pattern)
                clean_path = self._clean_url_path(pattern_path)
                urls.append({
                    'path': clean_path,
                    'name': pattern.name,
                    'callback': f"{pattern.callback.__module__}.{pattern.callback.__name__}"
                })
            elif isinstance(pattern, URLResolver):
                resolver_path = parent_path + str(pattern.pattern)
                urls.extend(self._collect_urls(pattern.url_patterns, resolver_path))
        return urls

    def _clean_url_path(self, path):
        """Clean regex characters from URL path for better readability."""
        # Remove common regex anchors and characters that don't represent actual URL parts
        cleaned = path
        
        # Remove regex anchors
        cleaned = cleaned.replace('^', '')
        cleaned = cleaned.replace('$', '')
        
        # Clean up multiple slashes
        while '//' in cleaned:
            cleaned = cleaned.replace('//', '/')
        
        # Ensure path starts with / if it's not empty
        if cleaned and not cleaned.startswith('/'):
            cleaned = '/' + cleaned
            
        # Remove trailing slash for consistency (except for root)
        if cleaned.endswith('/') and len(cleaned) > 1:
            cleaned = cleaned[:-1]
            
        return cleaned or '/'

    def _filter_and_group_admin_urls(self, all_urls, options):
        """Filter URLs containing 'admin' and group them by prefix."""
        admin_groups = {}
        
        for url in all_urls:
            path = url['path']
            if self.ADMIN_FILTER in path.lower():
                # Apply static/dynamic filtering if specified
                if not self._should_include_url(path, options):
                    continue
                    
                group_key = self._get_group_key(path)
                
                if group_key not in admin_groups:
                    admin_groups[group_key] = []
                admin_groups[group_key].append(url)
        
        return admin_groups

    def _should_include_url(self, path, options):
        """Check if URL should be included based on static/dynamic filters."""
        static_filter = options.get('static', False)
        dynamic_filter = options.get('dynamic', False)
        
        # If neither filter is specified, include all URLs
        if not static_filter and not dynamic_filter:
            return True
        
        has_dynamic = self._has_dynamic_parts(path)
        
        # If both filters are specified, include all URLs (contradictory filters)
        if static_filter and dynamic_filter:
            return True
        
        # Apply specific filter
        if static_filter:
            return not has_dynamic  # Include only static URLs
        elif dynamic_filter:
            return has_dynamic      # Include only dynamic URLs
        
        return True

    def _get_group_key(self, path):
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

    def _get_display_name(self, group_name):
        """Get the display name for a group."""
        return self.WAGTAIL_ADMIN_DISPLAY if group_name == self.WAGTAIL_ADMIN_KEY else group_name

    def _get_user_selection(self, admin_groups):
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

    def _display_group_menu(self, admin_groups):
        """Display the available admin URL groups menu."""
        self.stdout.write(self.style.SUCCESS("\nAvailable admin URL groups:"))
        
        group_list = sorted(admin_groups.keys())
        for i, group_name in enumerate(group_list, 1):
            count = len(admin_groups[group_name])
            display_name = self._get_display_name(group_name)
            self.stdout.write(f"{i}. {display_name} ({count} URLs)")
        
        self.stdout.write(f"{len(group_list) + 1}. {self.ALL_GROUPS_OPTION}")

    def _display_urls(self, selected_groups, options):
        """Display the selected URL groups with formatting."""
        if not selected_groups:
            return
        
        # Capture output for file writing if needed
        file_output = []
        write_to_file = options.get('tofile', False)
        
        for group_name, urls in selected_groups:
            self._display_group_section(group_name, urls, file_output if write_to_file else None)
        
        # Write to file if requested
        if write_to_file:
            self._write_to_file(file_output)

    def _display_group_section(self, group_name, urls, file_output=None):
        """Display a single group section with its URLs."""
        display_name = self._get_display_name(group_name)
        header = f"\n=== {display_name.upper()} URLs ==="
        subheader = f"Found {len(urls)} URLs in this group\n"
        
        # Display to console
        self.stdout.write(self.style.SUCCESS(header))
        self.stdout.write(subheader)
        self.stdout.write("")  # Extra line for spacing
        
        # Add to file output if capturing
        if file_output is not None:
            file_output.append(header)
            file_output.append(subheader)
            file_output.append("")
        
        sorted_urls = sorted(urls, key=lambda x: x['path'])
        current_prefix = None
        
        for url in sorted_urls:
            current_prefix = self._display_url_with_grouping(url, current_prefix, file_output)
        
        self.stdout.write('')  # Extra line between groups
        if file_output is not None:
            file_output.append('')

    def _display_url_with_grouping(self, url, current_prefix, file_output=None):
        """Display a single URL with grouping markers if needed."""
        path_parts = url['path'].strip('^').split('/')
        meaningful_parts = [part for part in path_parts if part]
        
        # Add grouping marker for URLs with multiple parts
        if len(meaningful_parts) >= 2:
            prefix = '/'.join(meaningful_parts[:2])
            
            if prefix != current_prefix:
                if current_prefix is not None:
                    self.stdout.write('')  # Extra line between prefix groups
                    if file_output is not None:
                        file_output.append('')
                
                marker_line = f"{self.SECTION_MARKER} {prefix}/..."
                self.stdout.write(self.style.HTTP_INFO(marker_line))
                if file_output is not None:
                    file_output.append(marker_line)
                current_prefix = prefix
        
        # Style and display the URL
        styled_path = self._get_styled_path(url['path'])
        faded_dot = self.style.HTTP_NOT_MODIFIED(self.SEPARATOR_DOT)
        
        console_line = f"Path: {styled_path} {faded_dot} Name: {url['name']} {faded_dot} View: {url['callback']}"
        self.stdout.write(console_line)
        
        # Add plain text version to file output
        if file_output is not None:
            file_line = f"Path: {url['path']} {self.SEPARATOR_DOT} Name: {url['name']} {self.SEPARATOR_DOT} View: {url['callback']}"
            file_output.append(file_line)
        
        return current_prefix

    def _get_styled_path(self, path):
        """Apply appropriate styling to URL path based on whether it has dynamic parts."""
        if self._has_dynamic_parts(path):
            return self.style.WARNING(path)
        else:
            return self.style.SUCCESS(path)

    def _has_dynamic_parts(self, path):
        """Check if URL path contains dynamic parts."""
        return ('<' in path and '>' in path) or ('(' in path and ')' in path)

    def _write_to_file(self, file_output):
        """Write the captured output to a file."""
        try:
            with open(self.OUTPUT_FILE_NAME, 'w', encoding='utf-8') as f:
                for line in file_output:
                    f.write(line + '\n')
            
            self.stdout.write(
                self.style.SUCCESS(f"\nOutput successfully written to {self.OUTPUT_FILE_NAME}")
            )
        except IOError as e:
            self.stdout.write(
                self.style.ERROR(f"Error writing to file {self.OUTPUT_FILE_NAME}: {e}")
            )
