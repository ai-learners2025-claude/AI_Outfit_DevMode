async function fetchGalleryFromBackend(source, shouldRender = true) {
  const cacheKey = `gallery-${globalUserId}-${source}`; // 生成一個唯一的緩存鍵

  try {
    // 嘗試從 localStorage 中讀取緩存資料
    const cachedData = localStorage.getItem(cacheKey);
    if (cachedData) {
      console.log("使用緩存資料");
      images = JSON.parse(cachedData); // 將緩存的資料轉換回圖片格式
      if (shouldRender) {
        renderGallery();
      } else {
        console.log("Gallery not rendered.");
      }
      return; // 如果有緩存資料，則直接返回
    }

    // 如果沒有緩存資料，則從後端請求資料
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

    // 儲存到 localStorage 中
    localStorage.setItem(cacheKey, JSON.stringify(images));

    // 根據 shouldRender 參數來決定是否渲染
    if (shouldRender) {
      renderGallery();
    } else {
      console.log("Gallery not rendered.");
    }

  } catch (error) {
    console.error("載入失敗", error);
    alert('載入圖片失敗');
  }
}
