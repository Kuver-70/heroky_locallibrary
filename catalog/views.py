from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from .models import Book, Author, BookInstance
from .forms import RenewBookForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Author


def index(request):
    """Display function for the home page of the site."""
    # Generation of "quantities" of some major objects.
    num_books=Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Available books (status = "a").
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.all().count()  # Method 'all()' is used by default.

    # Number of visits to this view, as counted in the session variable.
    num_visits=request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits+1


    # Drawing HTML-template with data inside var context.
    return render(
        request,
        'index.html',
        context={'num_books': num_books,
                 'num_instances': num_instances,
                 'num_instances_available': num_instances_available,
                 'num_authors': num_authors,
                 'num_visits': num_visits,
                 }
    )


class BookListView(generic.ListView):
    """Generic class-based view for a list of books."""
    model = Book
    paginate_by = 10


class BookDetailView(generic.DetailView):
    """Generic class-based detail view for a book."""
    model = Book


class AuthorListView(generic.ListView):
    """Generic class-based list view for a list of authors."""
    model = Author
    paginate_by = 10


class AuthorDetailView(generic.DetailView):
    """Generic class-based detail view for an author."""
    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to all users."""
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk = pk)

    # Если это POST-запрос, то обрабатываем данные Form
    if request.method == 'POST':

        # Создаем экземпляр формы и заполняем его данными с запроса (связываем - "биндим")
        form = RenewBookForm(request.POST)

        # Проверяем, валидна ли форма:
        if form.is_valid():
            # обрабатываем данные в form.cleaned_data как требовалось (здесь мы только записываем их в поле due-back модели)
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            # перенаправляем на новый URL:
            return HttpResponseRedirect(reverse('all-borrowed'))

    # Если это метод Get (или любой другой), то создаем форму по умолчанию.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial = {'date_of_death': '12/10/2016',}


class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')


class BookCreate(CreateView):
        model = Book
        fields = '__all__'


class BookUpdate(UpdateView):
        model = Book
        fields = '__all__'


class BookDelete(DeleteView):
        model = Book
        success_url = reverse_lazy('books')