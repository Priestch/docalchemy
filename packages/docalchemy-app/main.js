import { createViewerApp } from "@document-kits/viewer";
import {getDocumentUrl, getPagePredictions} from "./http";
import "@document-kits/viewer/viewer.css";
import "./assets/app.css";


const name = "600016";
let src = getDocumentUrl(name);
const appOptions = {
  parent: document.getElementById("app"),
  src,
  resourcePath: "document-viewer",
  disableCORSCheck: true,
  disableAutoSetTitle: true,
  appOptions: {
    textLayerMode: 0,
  }
};

// annotations
// :
// [{_annotation_id: "dd088056-c87b-3a90-bb2e-2bd80da6e33b", _category_name: "title", active: true,…},…]
// document_id
// :
// "0325fb96-c028-332e-abef-4c5797a611f0"
// embeddings
// :
// {75e5b7fc-0f36-3206-93b4-11d1701b5bc8: {absolute_coords: true, lrx: 2363, lry: 3226, ulx: 0, uly: 0}}
// external_id
// :
// null
// file_name
// :
// "10955_0.pdf"
// location
// :
// "/home/gaopeng/Enter/docalchemy/storage/pdf/10955.pdf"
// page_number
// :
// 0
// _annotation_ids
// :
// ["dd088056-c87b-3a90-bb2e-2bd80da6e33b", "ba7bd646-29fd-307d-99fc-44e92d30f952",…]
// _bbox
// :
// {absolute_coords: true, lrx: 2363, lry: 3226, ulx: 0, uly: 0}
// _image_id
// :
// "75e5b7fc-0f36-3206-93b4-11d1701b5bc8"
// _summary
// :
// null

/**
 * @typedef Image
 * @property {string} document_id
 * @property {any[]} embeddings
 * @property {number} page_number
 */

/**
 * @typedef BoundingBox
 * @property {boolean} absolute_coords
 * @property {number} ulx
 * @property {number} uly
 * @property {number} lrx
 * @property {number} lry
 */

/**
 * @typedef Annotation
 * @property {string} category_name
 * @property {BoundingBox} bounding_box
 * @property {Image} image
 * @property {number} score
 */

/**
 * @typedef Embeddings
 * @property {string} category_name
 * @property {BoundingBox} bounding_box
 * @property {Image} image
 * @property {number} score
 */


/**
 * @typedef {Object} PageData
 * @property {Annotation[]} annotations - The annotations
 * @property {string} document_id
 * @property {any} embeddings
 * @property {string} _image_id
 */

class PageViewport {
  /**
   * @param {BoundingBox} data
   */
  constructor(data) {
    this.data = data;
    this.width = Math.abs(data.lrx - data.ulx);
    this.height = Math.abs(data.lry - data.uly);
  }
}

class ImagePage {
  /**
   * @param {PageData} data
   * @param pdfViewport
   */
  constructor(data, pdfViewport) {
    this.data = data;
    this.pdfViewport = pdfViewport;
    this.viewport = new PageViewport(this.data.embeddings[this.data._image_id]);
    this.scale = this.viewport.width / pdfViewport.width;
  }

  getAnnotationDims(index) {
    const box = this.data.annotations[index].bounding_box;
    return {
      x: box.ulx / this.viewport.width,
      y: box.uly / this.viewport.height,
      width: (box.lrx - box.ulx) / this.viewport.width,
      height: (box.lry - box.uly) / this.viewport.height,
    };
  }
}

function registerEventHandler(viewerApp, name, handler) {
  viewerApp.initializedPromise.then(function () {
    viewerApp.eventBus.on(name, handler);
  })
}

function renderPredictions(pageNumber) {
  getPagePredictions(name, pageNumber).then((res) => {
    res.data.annotations.sort((a, b) => {
      return a.bounding_box.uly - b.bounding_box.uly;
    })
    const pageView = viewerApp.pdfViewer.getPageView(pageNumber - 1);
    const page = new ImagePage(res.data, pageView.viewport);

    const annotations = page.data.annotations;
    console.log(new Set(annotations.map(i => i.category_name)), annotations);
    const annotationEditorLayer = pageView.annotationEditorLayer.annotationEditorLayer;
    for (let i = 0; i < annotations.length; i++) {
      const annotation = annotations[i];
      // const excludeCategories = ['word', 'row', 'column', 'cell']
      const excludeCategories = ['word', 'row', 'column', 'cell', 'table']
      if (excludeCategories.includes(annotation.category_name)) {
        continue;
      }
      const dims = page.getAnnotationDims(i);
      const div = document.createElement('div');
      div.dataset.category = annotation.category_name;
      div.classList.add('annotation');
      // div.style.left = rect[0] + "px";
      div.style.left = `${dims.x * 100}%`;
      div.style.top = `${dims.y * 100}%`;
      div.style.width = `${dims.width * 100}%`;
      div.style.height = `${dims.height * 100}%`;
      if (annotation.category_name === 'table') {
        const tableEl = document.createElement('table');
        const tableText = annotation.sub_categories.html.value.join("");
        div.appendChild(tableEl)
        tableEl.outerHTML = tableText;
      } else {
        const categoryEl = document.createElement('span');
        categoryEl.classList.add('annotation__label')
        categoryEl.textContent = annotation.category_name;
        div.appendChild(categoryEl);
      }

      annotationEditorLayer.div.hidden = false;
      annotationEditorLayer.div.appendChild(div);
    }
  })
}

const viewerApp = createViewerApp(appOptions);
viewerApp.initializedPromise.then(function () {
  registerEventHandler(viewerApp, 'annotationeditorlayerrendered', function (evt) {
    renderPredictions(evt.pageNumber);
  })
})
