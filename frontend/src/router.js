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
import PhotoWall from "./components/PhotoWall";
import PersonsView from "./components/PersonsView";
import SimilarPersons from "./components/SimilarPersons";
import ThingsView from "./components/ThingsView";
import PlacesView from "./components/PlacesView";
import SearchView from "./components/SearchView";
import AlbumView from "./components/AlbumView";
import AlbumListView from "./components/AlbumListView";

Vue.use(Router);

export default new Router({
  routes: [

    {
      path: '/wall',
      name: 'photoWall',
      component: PhotoWall,
      /*
      props: route => ({ 
        personId: route.query.person_id, 
        thingId: route.query.thing_id,
        city: route.query.city,
        county: route.query.county,
        country: route.query.country,
        state: route.query.state,
        camera: route.query.camera,
        from: route.query.from,
        to: route.query.to,
        rating: route.query.rating,
        albumId: route.query.album_id
      })
      */
      props: castRouteParams
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
      path: '/search',
      name: 'search',
      component: SearchView
    },
    {
      path: '/album',
      name: 'album',
      component: AlbumView,
      props: castRouteParams
      /*
      props: route => ({ 
        albumId:route.query.album_id
      })*/
    },
    {
      path: '/albumlist',
      name: 'albumList',
      component: AlbumListView
    },

    {
      path: '*',
      redirect: '/wall'
    }
  ]
})

function castRouteParams(route) {
  return {
    personId: Number(route.query.person_id), 
    thingId: route.query.thing_id,
    city: route.query.city,
    county: route.query.county,
    country: route.query.country,
    state: route.query.state,
    camera: route.query.camera,
    from: route.query.from,
    to: route.query.to,
    rating: route.query.rating,
    albumId: Number(route.query.album_id),
    newAlbum: Boolean(route.query.newAlbum)
  };
}