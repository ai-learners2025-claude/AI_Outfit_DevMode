async function fetchGalleryFromBackend(source) {
  try {
    const res = await fetch(`/linebot/view_images/${globalUserId}/${source}/`);
    const data = await res.json();
    images = (data.images || []).map(item => {
      const img = {
        id: item.id,
        url: item.url.startsWith('/') ? item.url : '/' + item.url,
      };
      if (item.category) img.category = item.category;
      return img;
    });
    renderGallery();
  } catch (error) {
    console.error("載入失敗", error);
    alert('載入圖片失敗');
  }
}