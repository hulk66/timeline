// import axios from "axios";
export const photo = {
    state: {
        selectedSegment: Object,
        selectedSection: Object,
        selectedIndex: 0,
        selectedPhoto: Object,
        selectedPhotos: new Set(),

        lowerSelectionBound: {
            section: Number.MAX_VALUE,
            segment: Number.MAX_VALUE,
            index: Number.MAX_VALUE
        },

        upperSelectionBound: {
            section: 0,
            segment: 0,
            index: 0
        }
    },

    mutations: {
        setSelectedSegment(state, segment) {
            state.selectedSegment = segment;
        },
        setSelectedSection(state, section) {
            state.selectedSection = section;
        },
        setSelectedIndex(state, index) {
            state.selectedIndex = index;
        },
        setSelectedPhoto(state, photo) {
            state.selectedPhoto = photo;
        },

        navigate(state, dir) {
            state.selectedIndex += dir;
        },
        setSelectedPhotos(state, idArray) {
            state.selectedPhotos = idArray;
        }, 

        addPhotoToSelection(state, p) {
            // state.selectedPhotos.push(p);
            state.selectedPhotos.add(p);
        },

        removePhotoFromSelection(state, p) {
            state.selectedPhotos = state.selectedPhotos.filter(item => item.id !== p.id)
        },

        setSelectionBoundaries(state, { section, segment, index} ) {
            if (section < state.lowerSelectionBound.section) 
                setLowerBounds(state, section, segment, index)
            else if (section == state.lowerSelectionBound.section && segment < state.lowerSelectionBound.segment)
                setLowerBounds(state, section, segment, index)
            else if (section == state.lowerSelectionBound.section && segment == state.lowerSelectionBound.segment && index < state.lowerSelectionBound.index)
                setLowerBounds(state, section, segment, index)

            if (section > state.upperSelectionBound.section) 
                setUpperBounds(state, section, segment, index)
            else if (section == state.upperSelectionBound.section && segment > state.upperSelectionBound.segment)
                setUpperBounds(state, section, segment, index)
            else if (section == state.upperSelectionBound.section && segment == state.upperSelectionBound.segment && index > state.upperSelectionBound.index)
                setUpperBounds(state, section, segment, index)

        }
    },

    actions: {


    }
}

function setLowerBounds(state, section, segment, index) {
    state.lowerSelectionBound.section = section;
    state.lowerSelectionBound.segment = segment;
    state.lowerSelectionBound.index = index;
}

function setUpperBounds(state, section, segment, index) {
    state.upperSelectionBound.section = section;
    state.upperSelectionBound.segment = segment;
    state.upperSelectionBound.index = index;
}
