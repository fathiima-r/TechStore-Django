from django.contrib import admin

from .models import Category, Product, Banner, Order


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'description',
    )

    search_fields = (
        'name',
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'category',
        'price',
        'is_active',
        'created_at',
    )

    list_filter = (
        'category',
        'is_active',
    )

    search_fields = (
        'name',
        'description',
    )

    list_editable = (
        'is_active',
    )


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'title',
        'content',
    )

    list_editable = (
        'is_active',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'total_amount',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'user__username',
    )
