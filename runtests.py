#!/usr/bin/env python
"""
Convenience script to run tests for wagtail-unveil package.

This script provides an easy way to run tests with proper Django settings
and displays warnings. It's particularly useful during development to see
deprecation warnings and other issues.

Usage:
    python runtests.py                    # Run all wagtail_unveil tests
    python runtests.py test_views         # Run specific test module
    python runtests.py --verbose          # Run with verbose output
    python runtests.py --failfast         # Stop on first failure
    python runtests.py --debug-mode       # Run with DEBUG=True
    python runtests.py --help             # Show help
"""

import os
import sys
import warnings
import argparse


def setup_django():
    """Configure Django settings for testing."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_project.settings.base")
    
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    return settings, get_runner(settings), django


def run_tests(test_labels=None, verbosity=1, interactive=True, failfast=False, 
              keepdb=False, debug_mode=False, show_warnings=True):
    """
    Run the test suite with the specified options.
    
    Args:
        test_labels: List of test labels to run (default: ['wagtail_unveil'])
        verbosity: Verbosity level (0, 1, or 2)
        interactive: Whether to run in interactive mode
        failfast: Stop on first failure
        keepdb: Keep test database after tests
        debug_mode: Run with DEBUG=True
        show_warnings: Show Python warnings
    """
    if test_labels is None:
        test_labels = ['wagtail_unveil']
    
    # Configure warnings
    if show_warnings:
        # Show all warnings
        warnings.resetwarnings()
        warnings.simplefilter('always')
        # Make deprecation warnings more visible
        warnings.filterwarnings('always', category=DeprecationWarning)
        warnings.filterwarnings('always', category=PendingDeprecationWarning)
    
    settings, TestRunner, django = setup_django()
    
    # Override DEBUG setting if requested
    if debug_mode:
        settings.DEBUG = True
        print("Running tests with DEBUG=True")
    
    # Display test configuration
    print(f"Django version: {django.get_version()}")
    print(f"Python version: {sys.version}")
    print(f"Database: {settings.DATABASES['default']['ENGINE']}")
    print(f"Test labels: {test_labels}")
    print(f"Verbosity: {verbosity}")
    if show_warnings:
        print("Warnings: Enabled (use --no-warnings to disable)")
    print("-" * 60)
    
    # Run tests
    test_runner = TestRunner(
        verbosity=verbosity,
        interactive=interactive,
        failfast=failfast,
        keepdb=keepdb,
    )
    
    failures = test_runner.run_tests(test_labels)
    
    # Display summary
    print("-" * 60)
    if failures:
        print(f"Tests completed with {failures} failure(s)")
        return 1
    else:
        print("All tests passed!")
        return 0


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description='Run wagtail-unveil tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runtests.py                           # Run all wagtail_unveil tests
  python runtests.py test_views                # Run specific test module
  python runtests.py test_views.UnveilReportsIndexViewTest  # Run specific test class
  python runtests.py --verbose --failfast      # Verbose output, stop on first failure
  python runtests.py --debug-mode              # Run with DEBUG=True
  python runtests.py --keepdb                  # Keep test database for faster subsequent runs
        """
    )
    
    parser.add_argument(
        'test_labels',
        nargs='*',
        help='Specific test labels to run (default: wagtail_unveil)',
        default=['wagtail_unveil']
    )
    
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        choices=[0, 1, 2],
        default=1,
        help='Verbosity level: 0=minimal, 1=normal, 2=verbose (default: 1)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_const',
        const=2,
        dest='verbosity',
        help='Shortcut for --verbosity=2'
    )
    
    parser.add_argument(
        '--failfast',
        action='store_true',
        help='Stop running tests after first failure'
    )
    
    parser.add_argument(
        '--keepdb',
        action='store_true',
        help='Keep test database for faster subsequent runs'
    )
    
    parser.add_argument(
        '--debug-mode',
        action='store_true',
        help='Run tests with DEBUG=True'
    )
    
    parser.add_argument(
        '--no-warnings',
        action='store_true',
        help='Disable warning output'
    )
    
    parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Run in non-interactive mode'
    )
    
    args = parser.parse_args()
    
    # Handle test labels
    test_labels = args.test_labels
    if test_labels == ['wagtail_unveil']:
        # Default case - ensure we're running wagtail_unveil tests
        pass
    elif len(test_labels) == 1 and not test_labels[0].startswith('wagtail_unveil'):
        # If user specified a single label without the app prefix, add it
        if '.' not in test_labels[0]:
            test_labels[0] = f'wagtail_unveil.tests.{test_labels[0]}'
        elif not test_labels[0].startswith('wagtail_unveil'):
            test_labels[0] = f'wagtail_unveil.{test_labels[0]}'
    
    try:
        return run_tests(
            test_labels=test_labels,
            verbosity=args.verbosity,
            interactive=not args.no_interactive,
            failfast=args.failfast,
            keepdb=args.keepdb,
            debug_mode=args.debug_mode,
            show_warnings=not args.no_warnings,
        )
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\nError running tests: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
