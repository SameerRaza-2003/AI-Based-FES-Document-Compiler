const form = document.getElementById("uploadForm");
const uploadBtn = document.getElementById("uploadBtn");
const uploadSpinner = document.getElementById("uploadSpinner");
const preview = document.getElementById("preview");
const compileBtn = document.getElementById("compileBtn");
const compileSpinner = document.getElementById("compileSpinner");
const downloadLink = document.getElementById("downloadLink");
const modalImg = document.getElementById("modalImage");
let cropper;
let compiledUrl = "";

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast align-items-center text-white bg-primary border-0 position-fixed bottom-0 end-0 m-3 show";
  toast.role = "alert";
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.classList.remove("show");
    toast.remove();
  }, 3000);
}

form.onsubmit = async (e) => {
  e.preventDefault();
  preview.innerHTML = "";
  downloadLink.classList.add("d-none");
  compileBtn.classList.add("d-none");
  compiledUrl = "";

  uploadSpinner.classList.remove("d-none");
  uploadBtn.disabled = true;

  const formData = new FormData(form);
  const res = await fetch("/upload", { method: "POST", body: formData });
  const data = await res.json();

  data.forEach(item => {
    const div = document.createElement("div");
    div.className = "border p-2 text-center bg-white";
    div.style.width = "200px";
    div.dataset.id = item.filename;
    div.innerHTML = `
      <div class="position-relative">
        <img src="/static/uploads/${item.filename}" class="img-fluid mb-1 clickable-preview"/>
        <button class="btn btn-sm btn-danger position-absolute top-0 end-0 delete-btn" data-id="${item.filename}">&times;</button>
        <button class="btn btn-sm btn-warning position-absolute top-0 start-0 crop-btn" data-id="${item.filename}">✂️</button>
      </div>
      <small>${item.doc_type}</small>`;
    preview.appendChild(div);
  });

  Sortable.create(preview, {
    animation: 150,
    onEnd: () => {
      compiledUrl = "";
      showToast("Order changed. Please click Compile PDF again.");
      downloadLink.classList.add("d-none");
    }
  });

  compileBtn.classList.remove("d-none");
  uploadSpinner.classList.add("d-none");
  uploadBtn.disabled = false;
};

preview.addEventListener("click", async (e) => {
  const id = e.target.dataset.id;
  if (e.target.classList.contains("delete-btn")) {
    const div = e.target.closest("div[data-id]");
    preview.removeChild(div);
    await fetch(`/delete_image/${id}`, { method: "POST" });
    compiledUrl = "";
    showToast("Image removed. Please click Compile PDF again.");
    downloadLink.classList.add("d-none");
  }

  if (e.target.classList.contains("crop-btn")) {
    const src = `/static/uploads/${id}`;
    modalImg.src = src;
    modalImg.dataset.filename = id;

    modalImg.onload = () => {
      if (cropper) cropper.destroy();

      const modalElement = document.getElementById("imageModal");
      const modalInstance = new bootstrap.Modal(modalElement);
      modalInstance.show();

      setTimeout(() => {
        cropper = new Cropper(modalImg, {
          aspectRatio: NaN,
          viewMode: 1,
          autoCropArea: 1.0,
          responsive: true,
          zoomable: true,
          background: false,
          scalable: true,
          movable: true
        });
      }, 500);
    };
  }
});

document.getElementById("cropSaveBtn").onclick = async () => {
  const canvas = cropper.getCroppedCanvas();
  const blob = await new Promise(res => canvas.toBlob(res));
  const formData = new FormData();
  formData.append("image", blob);
  formData.append("filename", modalImg.dataset.filename);

  await fetch("/crop_image", { method: "POST", body: formData });

  const updatedImg = preview.querySelector(`img[src="/static/uploads/${modalImg.dataset.filename}"]`);
  if (updatedImg) {
    const timestamp = new Date().getTime();
    updatedImg.src = `/static/uploads/${modalImg.dataset.filename}?t=${timestamp}`;
  }

  const modalInstance = bootstrap.Modal.getInstance(document.getElementById("imageModal"));
  modalInstance.hide();
};

compileBtn.onclick = async () => {
  compileSpinner.classList.remove("d-none");
  compileBtn.disabled = true;
  downloadLink.classList.add("d-none");

  const ordered = [...preview.children].map(div => div.dataset.id);
  const res = await fetch("/generate_pdf", {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ordered })
  });

  const data = await res.json();
  compiledUrl = data.url;

  downloadLink.href = compiledUrl;
  downloadLink.classList.remove("d-none");

  compileSpinner.classList.add("d-none");
  compileBtn.disabled = false;
};

document.addEventListener("click", function(e) {
  if (e.target.tagName === "IMG" && e.target.classList.contains("clickable-preview")) {
    const src = e.target.src;
    const modal = document.getElementById("imagePreviewModal");
    const enlargedImage = document.getElementById("enlargedImage");
    enlargedImage.src = src;
    modal.style.pointerEvents = "auto";
    modal.style.display = "flex";
    setTimeout(() => {
      modal.style.opacity = "1";
    }, 10);
  }
});

document.getElementById("closeImagePreview").addEventListener("click", () => {
  const modal = document.getElementById("imagePreviewModal");
  modal.style.opacity = "0";
  setTimeout(() => {
    modal.style.display = "none";
    modal.style.pointerEvents = "auto";
  }, 300);
});

document.getElementById("imagePreviewModal").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) {
    e.currentTarget.style.opacity = "0";
    e.currentTarget.style.pointerEvents = "none";
    setTimeout(() => {
      e.currentTarget.style.display = "none";
    }, 300);
  }
});

document.addEventListener("keydown", function(e) {
  if (e.key === "Escape") {
    const modal = document.getElementById("imagePreviewModal");
    if (modal.style.display === "flex") {
      modal.style.opacity = "0";
      modal.style.pointerEvents = "none";
      setTimeout(() => {
        modal.style.display = "none";
      }, 300);
    }
  }
});
