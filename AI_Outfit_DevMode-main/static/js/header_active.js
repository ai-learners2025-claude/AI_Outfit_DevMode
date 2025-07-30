document.addEventListener("DOMContentLoaded", function () {
  const links = document.querySelectorAll('.nav-icons a');
  const currentUrl = window.location.pathname;
  links.forEach(link => {
    const linkUrl = new URL(link.href);
    if (linkUrl.pathname === currentUrl) {
      link.classList.add('active');
    }
  });
});