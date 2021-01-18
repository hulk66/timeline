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

    <v-card v-intersect="{handler:onIntersect, options: {rootMargin:'1000px'}}" :min-height="initialHeight"  elevation="0">
        <div v-if="visible" ref="segmentContainer">
            <photo-segment :ref="'segment' + index"
                            v-for="(segment, index) in segments"
                           :segment="segment"
                           :key="index"
                           :target-height="targetHeight"
                            @select-photo="selectPhoto"
                            @update-timeline="updateTimeline">
            </photo-segment>
        </div>
        <div v-else></div>
    </v-card>

</template>

<script>

    import axios from "axios";
    import moment from "moment"

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
            state: String
        },
        data() {
            return {
                segments: [],
                visible: false,
                h: 0
            };
        },

        computed: {
        },
        mounted() {
            this.h = this.initialHeight;
        },

        watch: {

        },

        methods: {

            updateTimeline(currentDate) {
                this.$emit("update-timeline", currentDate)
            },
            selectPhoto(segment, photoIndex) {
                this.$emit("select-photo", this.section, segment, photoIndex)
            },

            advanceSegment(segment, dir) {
                let segment_nr = segment.nr + dir;
                if (segment_nr >= 0 && segment_nr < this.segments.length) {
                    let el = this.$refs['segment' + segment_nr][0]
                    if (dir == 1)
                        el.selectPhoto(0)
                    else
                        el.selectLastPhoto()
                    return el.segment;
                }
                return null;

            },

            selectFirstPhoto() {
                this.$refs.segment0[0].selectPhoto(0);
            },
            selectLastPhoto() {
                let len = this.segments.length-1
                let last_index = this.segments[len].photos.length-1;
                this.$refs['segment' + len][0].selectPhoto(last_index);
            },

            loadPhotos(sec) {
                let self = this;
                // eslint-disable-next-line no-console
                console.log("Loading photos for section " + sec.id);
                let params = {};
                let config ={ params: params};
                // if (this.filterPersonId)
                params["person_id"] = this.filterPersonId;
                // if (this.filterThingId)
                params["thing_id"] = this.filterThingId;

                params["city"] = this.city;
                params["county"] = this.county;
                params["country"] = this.country;
                params["state"] = this.state;


                axios.get( "/api/photo/by_section/" + sec.id, config).then((result) => {
                    self.photos = result.data;
                    self.segments = self.computeSegments()
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