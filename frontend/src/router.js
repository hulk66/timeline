/*
 * Copyright (C) 2021 Tobias Himstedt
 * 
 * 
 * This file is part of Timeline.
 * 
 * Timeline is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * Timeline is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import Vue from 'vue'
import Router from 'vue-router'
import PhotoWallSection from "./components/PhotoWallSection";
import PersonsView from "./components/PersonsView";
import SimilarPersons from "./components/SimilarPersons";
import ThingsView from "./components/ThingsView";
import PlacesView from "./components/PlacesView";

Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/wall',
      name: 'photoWall',
      component: PhotoWallSection,
      props:true
    },


    {
      path: '/persons',
      name: 'persons',
      component: PersonsView
    },
    {
      path: '/things',
      name: 'things',
      component: ThingsView
    },
    {
      path: '/places',
      name: 'places',
      component: PlacesView
    },
    {
      path: '/similarPersons',
      name: 'similarPersons',
      component: SimilarPersons
    },

    {
      path: '*',
      redirect: '/wall'
    }
  ]
})