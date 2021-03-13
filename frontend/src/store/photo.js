// import axios from "axios";
export const photo = {
    state: {
        selectedSegment: Object,
        selectedSection: Object,
        selectedIndex: 0,
        selectedPhoto: Object,

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
        }

    },

    actions: {


    }
}
  