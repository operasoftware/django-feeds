# Admin bindings
from djangofeeds.models import Feed, Post, Enclosure, Category
from django.contrib import admin


class FeedAdmin(admin.ModelAdmin):
    list_display = ('name', 'feed_url', 'date_last_refresh', 'is_active')
    search_fields = ['feed_url', 'name']


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'link', 'author', 'date_updated',
                    'date_published')
    search_fields = ['link', 'title']
    date_hierarchy = 'date_updated'

admin.site.register(Category)
admin.site.register(Enclosure)
admin.site.register(Feed, FeedAdmin)
admin.site.register(Post, PostAdmin)
