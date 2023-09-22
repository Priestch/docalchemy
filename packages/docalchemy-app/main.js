import { createViewerApp } from "@document-kits/viewer";
import {getDocumentUrl, getPagePredictions} from "./http";
import "@document-kits/viewer/viewer.css";
import "./assets/app.css";


const name = "10955";
let src = getDocumentUrl(name);
const appOptions = {
  parent: document.getElementById("app"),
  src,
  resourcePath: "document-viewer",
  disableCORSCheck: true,
  disableAutoSetTitle: true,
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

  getRect(boundingBox) {
    return [boundingBox.ulx, boundingBox.uly, boundingBox.lrx, boundingBox.lry].map((i) => i / this.scale);
  }

  getAnnotationRect(index) {
    const annotation = this.data.annotations[index];
    return this.getRect(annotation.bounding_box);
  }
}

function renderPredictions(pageNumber) {
  getPagePredictions(name, pageNumber).then((res) => {
    const pageView = viewerApp.pdfViewer.getPageView(pageNumber - 1);
    const page = new ImagePage(res.data, pageView.viewport);

    const annotations = page.data.annotations;
    console.log(new Set(annotations.map(i => i.category_name)));
    for (let i = 0; i < annotations.length; i++) {
      const annotation = annotations[i];
      const excludeCategories = ['word', 'row', 'column', 'cell']
      if (excludeCategories.includes(annotation.category_name)) {
        continue;
      }
      const rect = page.getAnnotationRect(i);
      const div = document.createElement('div');
      div.style.position = "absolute";
      div.style.border = "1px solid red";
      div.style.left = rect[0] + "px";
      div.style.top = rect[1] + "px";
      div.style.width = Math.ceil((rect[2] - rect[0])) + "px";
      div.style.height = Math.ceil((rect[3] - rect[1])) + "px";
      pageView.div.appendChild(div);
    }
  })
}

const viewerApp = createViewerApp(appOptions);
viewerApp.initializedPromise.then(function () {
  viewerApp.eventBus.on('documentinit', function () {
    console.log('isReady', viewerApp);
    viewerApp.eventBus.on('pagerendered', async function (evt) {
      console.log("pagerendered", evt);
      renderPredictions(evt.pageNumber);
    });
  })
})
