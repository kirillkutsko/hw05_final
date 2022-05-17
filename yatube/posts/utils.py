from django.core.paginator import Paginator

from yatube.settings import POST_PER_PAGE


def paginator(request, post_list):
    paginator = Paginator(post_list, POST_PER_PAGE)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj
