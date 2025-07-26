from django.contrib import admin
from .models import ClosetItem, MimicItem
from django import forms

@admin.register(ClosetItem)
class ClosetItemAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'category', 'image', 'uploaded_at')  # 移掉 image_preview

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True  # 允許多選

class MimicItemMultiUploadForm(forms.ModelForm):
    image = forms.ImageField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=True,
        label='圖片 (可多選)'
    )

    class Meta:
        model = MimicItem
        fields = ('user_id', 'image')

@admin.register(MimicItem)
class MimicItemAdmin(admin.ModelAdmin):
    form = MimicItemMultiUploadForm
    list_display = ('user_id', 'image', 'uploaded_at')

    def save_model(self, request, obj, form, change):
        images = request.FILES.getlist('image')
        user_id = form.cleaned_data.get('user_id')

        if images:
            # 多張圖都分別存一筆
            for image in images:
                MimicItem.objects.create(user_id=user_id, image=image)
        else:
            super().save_model(request, obj, form, change)