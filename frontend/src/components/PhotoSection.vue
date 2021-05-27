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
<template>
    <!-- 
        Somehow this rootMargin doesn't work. 
        The Intersection handler is called exactly when a card enters or leave the visible space
        Would expect this to happen "500px" earlier but for some reason it's not working
    -->
    <v-card v-intersect="{handler:onIntersect, options: {rootMargin:'500px'}}" ref="card" :min-height="initialHeight" elevation="0" > 
        <photo-segment  :ref="'segment' + index"
                        v-for="(segment, index) in segments"
                        :seg-index="index"
                        :data="segment"
                        :key="index"
                        :target-height="targetHeight"
                        @click-photo="clickPhoto"
                        @select-photo="selectPhotoEvent"
                        @select-multi="selectMultiEvent"
                        @update-timeline="updateTimeline">
        </photo-segment>
    </v-card>
</template>

<script>

    import axios from "axios";
    import moment from "moment"
    import {isReallyVisible} from "./Util";

    import PhotoSegment from "./PhotoSegment";
    export default {
        name: "PhotoSection",

        components: {
            PhotoSegment
        },

        props: {
            section: Object,
            index: Number,
            targetHeight: Number,
            initialHeight: Number,
            filterPersonId: Number,
            filterThingId: String,
            city: String,
            county: String,
            country: String,
            state: String,
            from: String,
            to: String,
            rating: Number,
            camera: String,
            filterAlbumId: Number
        },
        data() {
            return {
                segments: [],
                visible: false,
            };
        },

        computed: {
        },
        mounted() {
            // this.createObserver();
        },

        watch: {

        },

        methods: {

            getSegment(index) {
                return this.segments[index];
            },
            
            getSegmentEl(index) {
                return this.$refs['segment' + index][0];
            },
            createObserver() {
                let observer;
                let root = this.$parent.$parent.$el;
                let options = {
                    root: root,
                    rootMargin: "200px",
                };

                observer = new IntersectionObserver(this.onIntersect, options);
                observer.observe(this.$refs.card.$el);
            },
            findFirstVisibleSegment() {
                let segementElement = null;
                for (let i=0; i<this.segments.length; i++) {
                    segementElement = this.$refs['segment' + i][0]
                    if (isReallyVisible(segementElement.$el, false, this.targetHeight))        
                        break;
                }
                return segementElement;              
            },

            updateTimeline(currentDate) {
                this.$emit("update-timeline", currentDate)
            },

            clickPhoto(segment, photoIndex) {
                this.$emit("click-photo", this.section, segment, photoIndex)
            },

            selectPhotoEvent(segment, index, value) {
                this.$emit("select-photo", this.section, segment, index, value)
            },
            
            selectMultiEvent() {
                this.$emit("select-multi");
            },

            getFirstSegment() {
                return this.$refs.segment0[0];
            },

            getLastSegment() {
                let len = this.segments.length-1;
                let segment = this.$refs['segment' + len][0];
                return segment;
            },
            
            isVisible() {
                return this.visible
            },
            
            nextSegment(segment, dir) {

                let segment_nr = segment.data.nr + dir;
                if (segment_nr >= 0 && segment_nr < this.segments.length) {
                    let el = this.$refs['segment' + segment_nr][0]
                    return el;
                }
                return null;
            },
            advanceSegment(segment, dir) {
                let el = this.nextSegment(segment, dir);
                if (el) {
                    if (dir == 1)
                        el.clickPhoto(0)
                    else
                        el.clickLastPhoto()

                }
                return el;
            },

            
            clickFirstPhoto() {
                this.$refs.segment0[0].clickPhoto(0);
            },

            getFirstPhoto() {
                return  this.$refs.segment0[0].getFirstPhoto();
            },

            getLastPhoto() {
                let len = this.segments.length-1
                // let last_index = this.segments[len].photos.length-1;
                let segment = this.$refs['segment' + len][0];
                return segment.getLastPhoto(); 
            },

            clickLastPhoto() {
                let len = this.segments.length-1
                let last_index = this.segments[len].photos.length-1;
                this.$refs['segment' + len][0].clickPhoto(last_index);
            },

            loadPhotos(sec) {
                // eslint-disable-next-line no-console
                // console.log("Loading photos for section " + sec.id);
                let params = {};
                let config ={ params: params};
                if (!isNaN(this.filterPersonId))
                    params["person_id"] = this.filterPersonId;
                params["thing_id"] = this.filterThingId;
                params["city"] = this.city;
                params["county"] = this.county;
                params["country"] = this.country;
                params["state"] = this.state;
                params["from"] = this.from;
                params["to"] = this.to;
                params["camera"] = this.camera;
                params["rating"] = this.rating;
                if (!isNaN(this.filterAlbumId))
                    params["album_id"] = this.filterAlbumId;


                axios.get( "/api/photo/by_section/" + sec.id, config).then((result) => {
                    this.photos = result.data;
                    this.segments = this.computeSegments()
                })

            },
            // eslint-disable-next-line no-unused-vars
            onIntersect(entries, observer) {
                let element = entries[0];

                if (element.isIntersecting) {
                    if (!this.photos || this.photos.length == 0)
                        this.loadPhotos(this.section);
                    this.visible = true;
                    // eslint-disable-next-line no-console
                    // console.log(this.section.id + " visible");
                } else {
                    // eslint-disable-next-line no-console
                    // console.log(this.section.id + " invisible");
                    this.photos = [];
                    this.visible = false;
                }
            },
            computeSegments() {
                if (! this.photos)
                    return [];
                let res = [];
                let curElement= {};
                let prevDate = null;
                let nr = 0;
                this.photos.forEach( photo => {
                    let currentDate = moment(photo.created).startOf("day")

                    if (!prevDate || moment(currentDate).isBefore(prevDate)) {
                        prevDate = currentDate;
                        curElement = new Object()
                        curElement.date = currentDate.toDate();
                        curElement.photos = [];
                        curElement.nr = nr++;
                        res.push(curElement)
                    }
                    let ar = photo.width / photo.height;
                    photo.height = this.targetHeight;
                    photo.width = ar * this.targetHeight;

                    curElement.photos.push(photo);
                });
                return res;
            },

        }

    }
</script>
<style scoped>

</style>