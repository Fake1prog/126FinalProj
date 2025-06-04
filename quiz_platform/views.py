from django.shortcuts import render
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("""
    <html>
        <body>
            <h1>Quiz Show Platform</h1>
            <p>Frontend is being set up...</p>
            <a href="/admin/">Admin Panel</a><br>
            <a href="/api/">API Browser</a>
        </body>
    </html>
    """)