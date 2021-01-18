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
    <div ref="container" v-resize="resize">
        <v-subheader>{{segmentDate}}</v-subheader>
        <vue-justified-layout
                :items="segment.photos"
                v-slot="{item, index}"
                :options="{
                    targetRowHeight: targetHeight,
                    containerWidth: contWidth,
                    boxSpacing: 5,
                    containerPadding:10}">
            <img @click="selectPhoto(index)" :src="thumbSrc(item)" height="100%" width="100%"  v-intersect="{handler:onIntersect}">
        </vue-justified-layout>
    </div>
</template>
<script>

    import moment from "moment";
    export default {

        name: "PhotoSegment",

        components: {
            // ImageViewer,
            // VueJustifiedLayout
        },

        props: {
            segment: null,
            targetHeight: Number
        },
        data() {
            return {
                selectedIndex: 0,
                contWidth: 1060
            };
        },

        mounted() {
        },

        computed: {
            segmentDate() {
                return moment(this.segment.date).format("dddd, D.M.YYYY")
            }

        },
        watch: {

        },

        methods: {

            // eslint-disable-next-line no-unused-vars
            onIntersect(entries, observer) {
                let element = entries[0];
                if (element.isIntersecting) {
                    this.$emit('update-timeline', this.segment.date)
                }
            },
            resize() {
                this.contWidth = this.$refs.container.clientWidth;
            },
            thumbSrc(photo) {
                if (photo)
                    // return "/api/photo/preview/" + this.targetHeight +  "/" + photo.id + ".jpg";
                    // return "/photos/preview/" + this.targetHeight +  "/" + photo.path;
                    // return encodeURI("/photos/preview/" + this.targetHeight +  "?path=" + photo.path);
                    return encodeURI("/photos/preview/" + this.targetHeight + "/" + photo.path);
                else
                    return null;
            },

            selectPhoto(index) {
                this.$emit("select-photo", this.segment, index)
            },

            selectLastPhoto() {
                this.selectPhoto( this.segment.photos.length-1);
            }


        }
    }
</script>
<style scoped>

</style>