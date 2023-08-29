
export const url_utils = {

    elementVisibility(elementCss, show) {
        const els = document.querySelectorAll(elementCss);
        if (els && els.length > 0) {
            if (show) {
                els[0].style.visibility = 'visible';
            } else {
                els[0].style.visibility = 'hidden';
            }
        }
    }
};
