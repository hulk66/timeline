/*
 * Copyright (C) 2021, 2022 Tobias Himstedt
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
    <v-card ref="section" :min-height="initialHeight" flat
        v-intersect="{handler:onIntersect, options: {rootMargin:'100%'}}">
        <!--
        <v-card-title>{{section.id}}</v-card-title>
        -->
        <div class="d-flex flex-wrap justify-space-between">
            <segment 
                :scrollTo="segment == scrollToSegment"
                :ref="'segment' + index"
                v-for="(segment, index) in segments"
                :seg-index="index"
                :segment="segment"
                :key="index"
                :target-height="targetHeight"
                @click-photo="clickPhoto"
                @select-photo="selectPhotoEvent"
                @select-multi="selectMultiEvent"
                @update-timeline="updateTimeline">
            </segment>            
        </div>  
    </v-card>

</template>

<script>

    import axios from "axios";
    import moment from "moment"
    import {isReallyVisible} from "./Util";

    import Segment from "./Segment";
    export default {
        name: "AssetSection",

        components: {
            Segment,
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
            filterAlbumId: Number,
        },
        data() {
            return {
                segments: [],
                visible: false,
                scrollToSegment: null
            };
        },

        computed: {
            rootMargin() {
                return (this.targetHeight * 5).toString() + "px";
            }
        },
        mounted() {
        },

        watch: {

        },

        methods: {

            scrollTo(selectedDate) {            
                this.scrollToDate = selectedDate 
                this.$el.scrollIntoView();
            },


            getSegment(index) {
                return this.segments[index];
            },
            
            getSegmentEl(index) {
                return this.$refs['segment' + index][0];
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

            clickPhoto(segment, assetIndex) {
                this.$emit("click-photo", this.section, segment, assetIndex)
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

                let segment_nr = segment.segment.nr + dir;
                if (segment_nr >= 0 && segment_nr < this.segments.length) {
                    let el = this.$refs['segment' + segment_nr][0]
                    return el;
                }
                return null;
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
                let last_index = this.segments[len].Photos.length-1;
                this.$refs['segment' + len][0].clickPhoto(last_index);
            },

            loadAssets() {
                // eslint-disable-next-line no-console
                // console.log("Loading Photos for section " + sec.id);
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


                axios.get( process.env.BASE_URL + "api/asset/by_section/" + this.section.id, config).then((result) => {
                    this.assets = result.data;
                    this.segments = this.computeSegments();
                    if (this.scrollToDate) {
                        this.scrollToSegment = this.findSegment(this.scrollToDate);
                        this.scrollToDate = null;
                    } 

                })

            },

            assertAssetsLoad() {
                if (this.segments.length == 0)
                    this.loadAssets()
            },
            // eslint-disable-next-line no-unused-vars
            onIntersect(entries, observer, isIntersecting) {
                if (isIntersecting) {
                    this.loadAssets();
                    this.visible = true;
                    // eslint-disable-next-line no-console
                    // console.log("Section " + this.section.id + " visible");
                } else {
                    // eslint-disable-next-line no-console
                    // console.log("Section " + this.section.id + " invisible");
                    this.segments = [];
                    this.visible = false;
                }

            },

            computeSegments() {
                if (! this.assets)
                    return [];
                let res = [];
                let curElement= {};
                let prevDate = null;
                let nr = 0;
                this.assets.forEach( asset => {
                    let currentDate = moment(asset.created).startOf("day")

                    if (!prevDate || moment(currentDate).isBefore(prevDate)) {
                        prevDate = currentDate;
                        curElement = new Object()
                        curElement.date = currentDate.toDate();
                        curElement.assets = [];
                        curElement.nr = nr++;
                        res.push(curElement)
                    }
                    // let ar = asset.width / asset.height;
                    // asset.height = this.targetHeight;
                    // asset.width = ar * this.targetHeight;

                    curElement.assets.push(asset);
                });
                return res;
            },
            findSegment(date) {
                // can by optimized by divide and conquer approach
                for (let i=0; i<this.segments.length-1; i++) {
                    const current = this.segments[i];
                    const older = this.segments[i+1];
                    if (moment(date).isBetween(older.date, current.date))
                        return current;
                }
                return null;
            },

        }

    }
</script>
<style scoped>

</style>