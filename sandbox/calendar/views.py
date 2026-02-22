import calendar
import datetime

from django.shortcuts import render


def index(request):
    today = datetime.date.today()
    cal = calendar.HTMLCalendar(firstweekday=calendar.MONDAY)
    year_html = cal.formatyear(today.year, width=3)
    return render(
        request,
        "calendar/index.html",
        {
            "year": today.year,
            "calendar_html": year_html,
        },
    )


def month(request):
    today = datetime.date.today()
    cal = calendar.HTMLCalendar(firstweekday=calendar.MONDAY)
    month_html = cal.formatmonth(today.year, today.month)
    return render(
        request,
        "calendar/month.html",
        {
            "year": today.year,
            "month_name": calendar.month_name[today.month],
            "calendar_html": month_html,
        },
    )
