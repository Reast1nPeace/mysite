import datetime

from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.cache import cache
from read_statistics.utils import get_seven_days_read_data,\
    get_today_hot_data, get_yesterday_hot_data
from blog.models import Blog


def get_7_days_hot_blogs():
    today = timezone.now().date()
    date = today - datetime.timedelta(days=6)
    blogs = Blog.objects.filter(read_details__date__lte=today, read_details__date__gte=date) \
                        .values("id","title").annotate(read_num_sum=Sum("read_details__read_num")) \
                        .order_by("-read_num_sum")
    return blogs[:7]

def home(request):
    blog_content_type = ContentType.objects.get_for_model(Blog)
    dates, read_nums = get_seven_days_read_data(blog_content_type)

    #获取本周热门博客缓存
    hot_data_for_7_days = cache.get("hot_data_for_7_days")
    if hot_data_for_7_days is None:
        hot_data_for_7_days = get_7_days_hot_blogs()
        cache.set("hot_data_for_7_days", hot_data_for_7_days, 3600)

    context = {}
    context["read_nums"] = read_nums
    context["dates"] = dates
    context["today_hot_data"] = get_today_hot_data(blog_content_type)
    context["yesterday_hot_data"] = get_yesterday_hot_data(blog_content_type)
    context["hot_data_for_7_days"] = hot_data_for_7_days
    return render(request, "home.html", context)


def search(request):
    search_words = request.GET.get('wd', '').strip()
    # 分词：按空格 & | ~
    condition = None
    for word in search_words.split(' '):
        if condition is None:
            condition = Q(title__icontains=word)
        else:
            condition = condition | Q(title__icontains=word)

    search_blogs = []
    if condition is not None:
        # 筛选：搜索
        search_blogs = Blog.objects.filter(condition)

    # 分页
    paginator = Paginator(search_blogs, 10)
    page_num = request.GET.get('page', 1)  # 获取url的页面参数（GET请求）
    page_of_blogs = paginator.get_page(page_num)

    context = {}
    context['search_words'] = search_words
    context['search_blogs_count'] = search_blogs.count()
    context['page_of_blogs'] = page_of_blogs
    return render(request, 'search.html', context)


