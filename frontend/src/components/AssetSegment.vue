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
    <div ref="segmentCont" 
        :id="'seg' + segIndex"
        v-intersect="{handler:onIntersect, options: {rootMargin:'1200px', root:this.$parent.$parent.$parent.$el}}" 
        v-resize="resize"
        > 
        <!--
        <div class="ma-2 text-h6">Width {{contWidth}}</div>
        <div class="ma-2 text-h6">Segment {{segIndex}}</div>
        -->
        <div class="ma-2 text-h6">{{segmentDate}} </div>
        <!-- v-intersect="{handler:onIntersect, options: {rootMargin:this.rootMargin, root:this.$parent.$el}}" -->

        <vue-justified-layout
                :items="data.assets"
                v-slot="{item, index}"
                :options="{
                    targetRowHeight: targetHeight,
                    containerWidth: contWidth,
                    boxSpacing: 5,
                    containerPadding:5}">
                <asset-brick 
                    v-if="visible"
                    :asset="item" 
                    :index="index" 
                    :ref="'p' + index"
                    @set-rating="setRating"
                    @click-photo="clickPhoto"
                    @mark-photo="markPhoto"
                    @select-photo="selectPhotoEvent"
                    @select-multi="selectMultiEvent">
                </asset-brick>
        </vue-justified-layout>
    </div>
</template>
<script>

    import moment from "moment";
    import {isReallyVisible}  from "./Util";
    import { mapState } from 'vuex'
    import AssetBrick from "./AssetBrick.vue"
    export default {

        name: "AssetSegment",

        components: {
            AssetBrick
        },

        props: {
            data: null,
            targetHeight: Number,
            segIndex: Number
        },
        data() {
            return {
                contWidth: 1060,
                hover: false,
                visible: false
            };
        },

        mounted() {
            console.log("Segment root: ", this.$parent.$parent.$parent.$el)
        },

        computed: {
            rootMargin() {
                return this.targetHeight.toString() + "px";
            },

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
                return photoElement.isVisible()
                // let result = isReallyVisible(photoElement.getImgElement(), true);
                // return photoElement.visible;
                // return result;
            },

            scrollToPhoto(index, dir) {
                let photoElement =  this.$refs['p' + index];
                photoElement.$el.scrollIntoView( dir == 1 ? false:true)

            },

            indexOfFirstVisiblePhoto() {
                let photoElement = null;
                let index = 0;
                for (let i=0; i<this.data.assets.length;i++) {
                    photoElement = this.$refs['p' + i]
                    
                    // if (isReallyVisible(photoElement.getImgElement(), true, this.targetHeight)) {
                    if (photoElement.isVisible()) {
                        index = i
                        break;
                    }
                }
                return index;
            },
            getPhotoLength() {
                return this.data.assets.length;
            },

            markPhoto(index, value) {
                let wallPhoto = this.$refs['p' + index];
                if (wallPhoto)
                    wallPhoto.mark(value);

            },
            selectPhoto(index, value) {
                let wallPhoto = this.$refs['p' + index];
                if (wallPhoto)
                    wallPhoto.selectPhoto(value);

            },

            selectPhotoEvent(index, value) {
                this.$emit("select-photo", this, index, value);
            },

            selectMultiEvent() {
                this.$emit("select-multi");
            },
            
            setRating(index, value) {
                let photo = this.data.assets[index];
                // let self = this;
                this.$store.dispatch("setRating", {photo: photo, stars: value}).then( result => {
                    this.$set(this.data.assets, index, result);
                    this.$store.commit("setSelectedPhoto", result);
                });
            },


            // eslint-disable-next-line no-unused-vars
            onIntersect(entries, observer) {
                let element = entries[0];
                if (element.isIntersecting) {
                    // console.log(element.target.id + " visible")
                    this.visible = true;
                    this.$emit('update-timeline', this.data.date)
                } else {
                    this.visible = false;
                    // console.log(element.target.id + " invisible")

                }
            },
            resize() {
                this.contWidth = this.$refs.segmentCont.clientWidth;
            },
            thumbSrc(photo) {
                return encodeURI("/assets/preview/" + this.targetHeight + "/" + photo.path);
            },

            clickPhoto(index) {
                this.$emit("click-photo", this, index)
            },
            getFirstPhoto() {
                return this.data.assets[0];
            },

            getLastPhoto() {
                return this.data.assets[this.data.assets.length-1];
            },
            clickLastPhoto() {
                this.clickPhoto( this.data.assets.length-1);
            }


        }
    }
</script>
<style scoped>
</style>