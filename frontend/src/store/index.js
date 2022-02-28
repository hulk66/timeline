
import Vue from 'vue';
import Vuex from 'vuex';
import { person } from "./person"
import { photo } from "./photo"
import { general } from "./general"

Vue.use(Vuex);

export const store = new Vuex.Store({
    modules: {
        person,
        photo,
        general
    }
});
