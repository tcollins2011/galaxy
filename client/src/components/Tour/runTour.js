import axios from "axios";
import { getAppRoot } from "onload";
import { mountVueComponent } from "utils/mountVueComponent";
import Tour from "./Tour";

// delays and maximum number of attempts to wait for element
const attempts = 100;
const delay = 200;

// return tour data
async function getTourData(tourId) {
    const url = `${getAppRoot()}api/tours/${tourId}`;
    const { data } = await axios.get(url);
    return data;
}

// returns the selected element
function getElement(selector) {
    return document.querySelector(selector);
}

// wait for element
function waitForElement(selector, resolve, reject, tries) {
    const el = getElement(selector);
    if (el) {
        resolve();
    } else if (tries > 0) {
        setTimeout(() => {
            waitForElement(selector, resolve, reject, tries - 1);
        }, delay);
    } else {
        console.error("Tours - Element not found.", selector);
        reject();
    }
}

// performs a click event on the selected element
function doClick(targets) {
    if (targets) {
        targets.forEach((selector) => {
            const el = getElement(selector);
            if (el) {
                el.click();
            } else {
                console.error("Tours - Click target not found.", selector);
            }
        });
    }
}

// insert text into the selected element
function doInsert(selector, value) {
    if (value !== null) {
        const el = getElement(selector);
        if (el) {
            el.value = value;
            const event = new Event("input");
            el.dispatchEvent(event);
        } else {
            console.error("Tours - Insert target not found.", selector);
        }
    }
}

// mount tours to body
function mountTour(props) {
    const container = document.createElement("div");
    const body = document.querySelector("body");
    body.append(container);
    const mountFn = mountVueComponent(Tour);
    return mountFn(props, container);
}

// executes tour
export async function runTour(tourId, tourData = null) {
    if (!tourData) {
        tourData = await getTourData(tourId);
    }
    const steps = [];
    Object.values(tourData.steps).forEach((step) => {
        steps.push({
            target: step.element,
            title: step.title,
            content: step.content,
            onBefore: () => {
                return new Promise((resolve, reject) => {
                    if (step.element) {
                        // wait for element before continuing tour
                        waitForElement(step.element, resolve, reject, attempts);
                    } else {
                        resolve();
                    }
                }).then(() => {
                    doClick(step.preclick);
                    doInsert(step.element, step.textinsert);
                });
            },
            onNext: () => {
                doClick(step.postclick);
            },
        });
    });
    return mountTour({ steps });
}