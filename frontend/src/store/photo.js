// import axios from "axios";
export const photo = {
    state: {
        selectedSegment: Object,
        selectedSection: Object,
        selectedIndex: 0,
        selectedPhoto: Object,
        selectedPhotos: []

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
            state.selectedPhotos.push(p);
        },

        removePhotoFromSelection(state, p) {
            state.selectedPhotos = state.selectedPhotos.filter(item => item.id !== p.id)
        }

    },

    actions: {


    }
}
  