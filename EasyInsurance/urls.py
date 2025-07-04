from django.urls import path
from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("login/", views.LoginPage.as_view(), name="login"),
    path("register/", views.RegisterPage.as_view(), name="register"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("upload/", views.UploadView.as_view(), name="upload"),
    path("insurances/", views.InsuranceListView.as_view(), name="insurance_list"),
    path("insurances/<int:insurance_id>/", views.InsuranceDetailView.as_view(), name="insurance_detail"),
    path("insurances/<int:insurance_id>/edit/", views.InsuranceEditView.as_view(), name="insurance_edit"),
    path("insurance/form/", views.InsuranceFormView.as_view(), name="insurance_form"),
]