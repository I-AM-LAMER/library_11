from typing import Any
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.core.paginator import Paginator

from .models import Book, Genre, Author, Client
from .forms import TestForm, RegistrationForm

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
    class CustomListView(ListView):
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


def create_view(model_class, context_name, template):
    def view(request):
        id_ = request.GET.get('id', None)
        target = model_class.objects.get(id=id_) if id_ else None
        return render(
            request,
            template,
            {
                context_name: target,
            }
        )
    return view

view_book = create_view(Book, 'book', 'entities/book.html')
view_author = create_view(Author, 'author', 'entities/author.html')
view_genre = create_view(Genre, 'genre', 'entities/genre.html')

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
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        print('GOT REGTISTER POST: ', request.POST)
        if form.is_valid():
            print('1')
            user = form.save()
            print('2')
            Client.objects.create(user=user)
            print('3')
            return redirect('homepage')
    else:
        form = RegistrationForm()
    return render(
        request,
        'registration/register.html',
        {'form': form},
    )