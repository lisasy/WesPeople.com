# Create your views here.
from django.shortcuts import render_to_response, redirect, render
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.db import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.contrib.gis.geos import *
from django.contrib.gis.measure import D
import urllib
import requests
import simplejson

from maps.models import Person
from maps.models import AuthUser

def index(request):
    """
    Display the main index map page, with option to filter by year
    """

    template_values = {}

    return render_to_response('maps/index.html', template_values)

def filter_year(request, from_year, to_year=""):
    """
    Filter by graduation years
    """

    template_values = {'from_year': from_year, 'to_year' : to_year}

    return render_to_response('maps/index.html', template_values)

def filter_near(request, location, year=None, distance=50):
    """
    Location string to geocode from mapquest. Distance in miles
    """
    url = "http://open.mapquestapi.com/geocoding/v1/address?key=Fmjtd%7Cluub2dutn9%2Cbn%3Do5-9u25gr&location=" + location
    r = requests.get(url)

    latlng = r.json()['results'][0]['locations'][0]['latLng']
    lat = latlng['lat']
    lng = latlng['lng']

    pnt = fromstr("POINT(%s %s)" % (lng, lat))

    people = Person.geolocated.filter(location__distance_lte=(pnt, D(mi=distance)))


    if year:
      people = people.filter(preferred_class_year=year)

    people = people[0:80]

    years = [p.preferred_class_year for p in Person.geolocated.distinct('preferred_class_year')]
    majors_list = [p.wesleyan_degree_1_major_1 for p in Person.geolocated.distinct('wesleyan_degree_1_major_1')]
    majors = []
    for major in majors_list:
      if major != "":
        majors.append(major)

    industries = [p.industry for p in Person.geolocated.distinct('industry')]

    ids = [p.pk for p in people]

    template_values = {'people': people, 'distance' : distance, 'location' :
        location, 'ids' : ids, 'lat': lat, "lng" : lng, 'years' : years,
        'majors': majors, 'industries' : industries}

    return render_to_response('maps/near_results.html', template_values)

def search(request):
    """
    search stuff perhaps?
    """

    if 'general' in request.GET:
        message = 'You\'re looking for '+ request.GET['general'] + '.'
    else:
        message = "You failed"

    template_values = {'test': 'hello',
                        'message' : message}

    return render_to_response('map.html', template_values)

class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

def register(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            match = Person.objects.filter(preferred_email=form['email'].value())
            msg = "You have created a new account at wespeople.com."
            if match:
                match[0].user = new_user
                match[0].save()
                msg += "\n\nWe have found an existing profile for you based on your email address."
            send_mail("New account created", msg,
              "<support@wespeople.com>", [form['email'].value()])
            return HttpResponseRedirect("/")
    else:
        form = UserCreateForm()
    return render(request, "registration/register.html", {
        'form': form,
    })
