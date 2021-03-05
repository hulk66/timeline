

export function isElementInViewport (el) {
    let rect = el.getBoundingClientRect();

    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) && /* or $(window).height() */
        rect.right <= (window.innerWidth || document.documentElement.clientWidth) /* or $(window).width() */
    );
}

/**
 * fullVisible=true only returns true if the all object rect is visible
 */
export function isReallyVisible(el, fullVisible, offset=0, prevRect=null) {
    if ( el.tagName == "HTML" )
            return true;
    let parentRect = el.parentNode.getBoundingClientRect();
    let rect = prevRect || el.getBoundingClientRect();
    let result = (
            ( fullVisible ? rect.top    >= parentRect.top    : rect.bottom - offset > parentRect.top ) &&
            ( fullVisible ? rect.left   >= parentRect.left   : rect.right  > parentRect.left ) &&
            ( fullVisible ? rect.bottom <= parentRect.bottom : rect.top  < parentRect.bottom ) &&
            ( fullVisible ? rect.right  <= parentRect.right  : rect.left   < parentRect.right ) &&
            isReallyVisible(el.parentNode, false, offset, rect)
    )
    return result;
}

export function isVisible(el, percentX = 100, percentY=100){
    var tolerance = 0.01;   //needed because the rects returned by getBoundingClientRect provide the position up to 10 decimals

    var elementRect = el.getBoundingClientRect();
    var parentRects = [];
    var element = el;

    while(element.parentElement != null){
        parentRects.push(element.parentElement.getBoundingClientRect());
        element = element.parentElement;
    }

    var visibleInAllParents = parentRects.every(function(parentRect){
        var visiblePixelX = Math.min(elementRect.right, parentRect.right) - Math.max(elementRect.left, parentRect.left);
        var visiblePixelY = Math.min(elementRect.bottom, parentRect.bottom) - Math.max(elementRect.top, parentRect.top);
        var visiblePercentageX = visiblePixelX / elementRect.width * 100;
        var visiblePercentageY = visiblePixelY / elementRect.height * 100;
        return visiblePercentageX + tolerance > percentX && visiblePercentageY + tolerance > percentY;
    });
    return visibleInAllParents;
}