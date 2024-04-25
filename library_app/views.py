from typing import Any
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.core.paginator import Paginator
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError

from .serializers import BookSerializer, AuthorSerializer, GenreSerializer
from .models import Book, Genre, Author, Client
from .forms import TestForm, RegistrationForm, AddFundsForm

def home_page(request):
    return render(
        request,
        'index.html',
        {
            'books': Book.objects.count(),
            'authors': Author.objects.count(),
            'genres': Genre.objects.count(),
        }
    )

def create_listview(model_class, plural_name, template):
    class CustomListView(LoginRequiredMixin, ListView):
        model = model_class
        template_name = template
        paginate_by = 10
        context_object_name = plural_name

        def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
            context = super().get_context_data(**kwargs)
            instances = model_class.objects.all()
            paginator = Paginator(instances, 10)
            page = self.request.GET.get('page')
            page_obj = paginator.get_page(page)
            context[f'{plural_name}_list'] = page_obj
            return context
    return CustomListView

def create_view(model_class, context_name, template, redirect_page):
    @login_required
    def view(request):
        id_ = request.GET.get('id', None)
        if not id_:
            return redirect(redirect_page)
        try:
            target = model_class.objects.get(id=id_) if id_ else None
        except ValidationError:
            return redirect(redirect_page)
        if not target:
            return redirect(redirect_page)
        context = {context_name: target}
        if model_class == Book:
            client = Client.objects.get(user=request.user)
            context['client_has_book'] = target in client.books.all()
        return render(
            request,
            template,
            context,
        )
    return view

view_book = create_view(Book, 'book', 'entities/book.html', 'books')
view_author = create_view(Author, 'author', 'entities/author.html', 'authors')
view_genre = create_view(Genre, 'genre', 'entities/genre.html', 'genres')

BookListView = create_listview(Book, 'books', 'catalog/books.html')
AuthorListView = create_listview(Author, 'authors', 'catalog/authors.html')
GenreListView = create_listview(Genre, 'genres', 'catalog/genres.html')


def form_test_page(request):
    context = {}
    for key in ('choice', 'text', 'number'):
        context[key] = request.GET.get(key, None)
    context['form'] = TestForm()

    return render(
        request,
        'pages/form_test.html',
        context,
    )

def register(request):
    errors = ''
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Client.objects.create(user=user)
            return redirect('homepage')
        else:
            errors = form.errors
    else:
        form = RegistrationForm()
    return render(
        request,
        'registration/register.html',
        {'form': form, 'errors': errors},
    )

class MyPermission(permissions.BasePermission):
    def has_permission(self, request, _):
        if request.method in ('GET', 'OPTIONS', 'HEAD'):
            return bool(request.user and request.user.is_authenticated)
        elif request.method in ('POST', 'DELETE', 'PUT'):
            return bool(request.user and request.user.is_superuser)
        return False

def create_viewset(model_class, serializer):
    class ViewSet(viewsets.ModelViewSet):
        queryset = model_class.objects.all()
        serializer_class = serializer
        authentication_classes = [TokenAuthentication]
        permission_classes = [MyPermission]

    return ViewSet

BookViewSet = create_viewset(Book, BookSerializer)
AuthorViewSet = create_viewset(Author, AuthorSerializer)
GenreViewSet = create_viewset(Genre, GenreSerializer)

@login_required
def profile(request):
    form_errors = ''
    client = Client.objects.get(user=request.user)
    if request.method == 'POST':
        form = AddFundsForm(request.POST)
        if form.is_valid():
            money = form.cleaned_data.get('money')
            if money > 0:
                client.money += money
                client.save()
                form_errors = f'You have added {money} to your account!'
            else:
                form_errors = 'you can only add positive amount of money'
    else:
        form = AddFundsForm()

    return render(
        request,
        'pages/profile.html',
        {
            'form': form,
            'form_errors': form_errors,
            'client_data': {'username': client.user.username, 'money': client.money},
            'client_books': client.books.all(),
        }
    )

@login_required
def buy(request):
    book_id = request.GET.get('id', None)
    if not book_id:
        return redirect('books')
    try:
        book = Book.objects.get(id=book_id) if book_id else None
    except ValidationError:
        return redirect('books')
    if not book:
        return redirect('books')
    client = Client.objects.get(user=request.user)
    
    if request.method == 'POST' and client.money >= book.price:
            client.books.add(book)
            client.money -= book.price
            client.save()

    return render(
        request,
        'pages/buy.html',
        {
            'client_has_book': book in client.books.all(),
            'money': client.money,
            'book': book,
        }
    )
