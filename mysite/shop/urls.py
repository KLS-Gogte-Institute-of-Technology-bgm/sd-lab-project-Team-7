from django.urls import path
from . import views
from .views import Login,Signup

urlpatterns = [
    path("",views.index,name="ShopHome"),
    path("about/",views.about,name="AboutUs"),
    path("contact/",views.contact,name="ContactUs"),
    path("tracker/",views.tracker,name="TrackingStatus"),
    path("Search/",views.Search,name="Search"),
    path("products/<int:myid>",views.productview,name="productview"),
    path("checkout/",views.checkout,name="checkout"),
    path("handlerequest/",views.handlerequest,name="HandleRequest"),
    path('signup/',Signup.as_view()),
    path('login/',Login.as_view(),name='login'),
    path("logout/",views.logout,name="logout"),
    path("login/forgot/", views.forgot, name="forgot"),
    path("login/changepwd/", views.changePwd, name="changePwd"),
    path("login/changepwd/success", views.successChanged, name="successChanged")
]
