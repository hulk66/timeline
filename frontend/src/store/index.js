
import Vue from 'vue';
import Vuex from 'vuex';
import { person } from "./person"
import { photo } from "./photo"

Vue.use(Vuex);

export const store = new Vuex.Store({
    modules: {
        person,
        photo
    }
});
