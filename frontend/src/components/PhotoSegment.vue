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
    <div ref="segmentCont" v-resize="resize">
        <v-subheader>{{segmentDate}} Segment {{segIndex}}</v-subheader>
        <vue-justified-layout
                :items="data.photos"
                v-slot="{item, index}"
                :options="{
                    targetRowHeight: targetHeight,
                    containerWidth: contWidth,
                    boxSpacing: 5,
                    containerPadding:5}">
                <photo-brick 
                    :photo="item" 
                    :index="index" 
                    :target-height="targetHeight" 
                    v-intersect="{handler:onIntersect}" 
                    :ref="'p' + index"
                    @set-rating="setRating"
                    @select-photo="selectPhoto">
                </photo-brick>
        </vue-justified-layout>
    </div>
</template>
<script>

    import moment from "moment";
    import {isReallyVisible}  from "./Util";
    import { mapState } from 'vuex'
    import PhotoBrick from "./PhotoBrick.vue"
    export default {

        name: "PhotoSegment",

        components: {
            PhotoBrick
        },

        props: {
            data: null,
            targetHeight: Number,
            segIndex: Number
        },
        data() {
            return {
                contWidth: 1060,
                hover: false
            };
        },

        mounted() {
        },

        computed: {
            segmentDate() {
                return moment(this.data.date).format("dddd, D.M.YYYY")
            },

            ...mapState({
                markMode: state => state.person.markMode,
            }),
        },
        watch: {

        },

        methods: {

            isVisible() {
                return isReallyVisible(this.$el, false);
            },

            photoIsVisible(index) {
                let photoElement =  this.$refs['p' + index];
                // let result = isReallyVisible(photoElement.getImgElement(), true);
                return photoElement.visible;
                // return result;
            },

            indexOfFirstVisiblePhoto() {
                let photoElement = null;
                let index = 0;
                for (let i=0; i<this.data.photos.length;i++) {
                    photoElement = this.$refs['p' + i]
                    
                    // if (isReallyVisible(photoElement.getImgElement(), true, this.targetHeight)) {
                    if (photoElement.visible) {
                        index = i
                        break;
                    }
                }
                return index;
            },
            getPhotoLength() {
                return this.data.photos.length;
            },

            markPhoto(index, value) {
                let wallPhoto = this.$refs['p' + index];
                if (wallPhoto)
                    wallPhoto.mark(value);

            },
            setRating(index, value) {
                let photo = this.data.photos[index];
                // let self = this;
                this.$store.dispatch("setRating", {photo: photo, stars: value}).then( result => {
                    this.data.photos[index] = result;
                    this.$set(this.data.photos, index, result)
                });
            },

            // eslint-disable-next-line no-unused-vars
            onIntersect(entries, observer) {
                let element = entries[0];
                if (element.isIntersecting) {
                    this.$emit('update-timeline', this.data.date)
                }
            },
            resize() {
                this.contWidth = this.$refs.segmentCont.clientWidth;
            },
            thumbSrc(photo) {
                return encodeURI("/photos/preview/" + this.targetHeight + "/" + photo.path);
            },

            selectPhoto(index) {
                this.$emit("select-photo", this, index)
            },

            selectLastPhoto() {
                this.selectPhoto( this.data.photos.length-1);
            }


        }
    }
</script>
<style scoped>
</style>