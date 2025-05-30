from django.core.management.base import BaseCommand
from django.urls import URLPattern, URLResolver

"""
Command to list all admin URLs in a Django project
This is a developer utility command that helps in debugging and understanding the URL structure
"""

class Command(BaseCommand):
    help = "Lists all admin URLs in the project"

    def handle(self, *args, **options):
        from django.urls import get_resolver
        resolver = get_resolver()
        
        def collect_urls(patterns, parent_path=''):
            urls = []
            for pattern in patterns:
                if isinstance(pattern, URLPattern):
                    # This is a URL pattern
                    pattern_path = parent_path + str(pattern.pattern)
                    urls.append({
                        'path': pattern_path,
                        'name': pattern.name,
                        'callback': f"{pattern.callback.__module__}.{pattern.callback.__name__}"
                    })
                elif isinstance(pattern, URLResolver):
                    # This is a URL resolver (includes other patterns)
                    resolver_path = parent_path + str(pattern.pattern)
                    urls.extend(collect_urls(pattern.url_patterns, resolver_path))
            return urls
        
        all_urls = collect_urls(resolver.url_patterns)
        
        # Filter for admin URLs and group them
        admin_groups = {}
        
        for url in all_urls:
            path = url['path']
            # Check if the URL contains admin-related paths
            if 'admin' in path.lower():
                # Extract the first part of the path to group by
                path_parts = path.strip('^').split('/')
                if path_parts:
                    first_part = path_parts[0]
                    # Group by common admin prefixes
                    if 'admin' in first_part.lower():
                        group_key = first_part
                    else:
                        # Look for admin in subsequent parts
                        for part in path_parts:
                            if 'admin' in part.lower():
                                group_key = part
                                break
                        else:
                            group_key = 'other-admin'
                    
                    if group_key not in admin_groups:
                        admin_groups[group_key] = []
                    admin_groups[group_key].append(url)
        
        # Show available groups and ask user which one to display
        if not admin_groups:
            self.stdout.write(self.style.WARNING("No admin URLs found in the project."))
            return
        
        self.stdout.write(self.style.SUCCESS("\nAvailable admin URL groups:"))
        group_list = list(admin_groups.keys())
        for i, group_name in enumerate(group_list, 1):
            count = len(admin_groups[group_name])
            # Display "wagtail-admin" instead of "admin" for better clarity
            display_name = "wagtail-admin" if group_name == "admin" else group_name
            self.stdout.write(f"{i}. {display_name} ({count} URLs)")
        
        self.stdout.write(f"{len(group_list) + 1}. All groups")
        
        # Get user input
        while True:
            try:
                choice = input(f"\nEnter your choice (1-{len(group_list) + 1}): ").strip()
                choice_num = int(choice)
                
                if choice_num == len(group_list) + 1:
                    # Show all groups
                    selected_groups = admin_groups.items()
                    break
                elif 1 <= choice_num <= len(group_list):
                    # Show specific group
                    selected_group = group_list[choice_num - 1]
                    selected_groups = [(selected_group, admin_groups[selected_group])]
                    break
                else:
                    self.stdout.write(self.style.ERROR(f"Please enter a number between 1 and {len(group_list) + 1}"))
            except (ValueError, KeyboardInterrupt):
                self.stdout.write(self.style.ERROR("\nOperation cancelled."))
                return
            except EOFError:
                self.stdout.write(self.style.ERROR("\nNo input received. Operation cancelled."))
                return
        
        # Print the selected URLs
        for group_name, urls in selected_groups:
            # Display "wagtail-admin" instead of "admin" for better clarity
            display_name = "wagtail-admin" if group_name == "admin" else group_name
            self.stdout.write(self.style.SUCCESS(f"\n=== {display_name.upper()} URLs ==="))
            self.stdout.write(f"Found {len(urls)} URLs in this group\n")
            
            # Sort URLs by path for consistent ordering
            sorted_urls = sorted(urls, key=lambda x: x['path'])
            
            # Track path prefixes to add markers
            current_prefix = None
            
            for url in sorted_urls:
                # Extract first 2 parts of the path for grouping
                path_parts = url['path'].strip('^').split('/')
                # Filter out empty parts
                meaningful_parts = [part for part in path_parts if part]
                
                # Only add markers for URLs with more than one meaningful part
                if len(meaningful_parts) >= 2:
                    prefix = '/'.join(meaningful_parts[:2])
                    
                    # Add marker if this is a new prefix group
                    if prefix != current_prefix:
                        if current_prefix is not None:
                            self.stdout.write('')  # Extra line between prefix groups
                        self.stdout.write(self.style.HTTP_INFO(f"▶ {prefix}/..."))
                        current_prefix = prefix
                
                # Check if URL has dynamic parts and apply appropriate styling
                path_text = url['path']
                if '<' in path_text and '>' in path_text:
                    # URL has dynamic parts (angle bracket syntax like <int:id>)
                    styled_path = self.style.WARNING(path_text)
                elif '(' in path_text and ')' in path_text:
                    # URL has regex capture groups
                    styled_path = self.style.WARNING(path_text)
                else:
                    # Static URL
                    styled_path = self.style.SUCCESS(path_text)
                
                # Output all URL info on a single line
                faded_dot = self.style.HTTP_NOT_MODIFIED("•")
                self.stdout.write(f"Path: {styled_path} {faded_dot} Name: {url['name']} {faded_dot} View: {url['callback']}")
            self.stdout.write('')  # Extra line between groups