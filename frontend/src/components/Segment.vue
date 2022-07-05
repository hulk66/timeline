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
    <div ref="segmentCont" 
        v-intersect="onIntersect"
        :id="'seg' + segIndex">
        <div class="mt-5 text-h6">{{segmentDate}} </div>        
        <div class="segment">
            <tile 
                v-for="(asset, index) in segment.assets" 
                :target-height="targetHeight" 
                :index="index" 
                :ref="'p' + index"
                @set-rating="setRating"
                @click-photo="clickPhoto"
                @mark-photo="markPhoto"
                @select-photo="selectPhotoEvent"
                @select-multi="selectMultiEvent"
                :asset="asset" 
                :key="asset.path">
            </tile>                    
        </div>
    </div>

</template>
<script>

    import moment from "moment";
    import {isReallyVisible}  from "./Util";
    import { mapState } from 'vuex'
    import Tile from "./Tile.vue"

    export default {

        name: "Segment",

        components: {
            Tile
        },

        props: {
            segment: Object,
            targetHeight: Number,
            segIndex: Number,
            scrollTo: Boolean
        },
        data() {
            return {
                hover: false,
                visible: false
            };
        },

        mounted() {
            if (this.scrollTo) {
                this.$el.scrollIntoView();
            }
        },

        computed: {

            segmentDate() {
                return moment(this.segment.date).format("dddd, D.M.YYYY")
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
                let photoElement =  this.$refs['p' + index][0];
                return photoElement.isVisible()
                // let result = isReallyVisible(photoElement.getImgElement(), true);
                // return photoElement.visible;
                // return result;
            },

            scrollToPhoto(index) {
                let photoElement =  this.$refs['p' + index][0];
                // photoElement.$el.scrollIntoView();
                // let b = (dir == 1) ? 'end':'start';
                // photoElement.$el.scrollIntoView( dir == 1 ? false:true)
                // photoElement.$el.scrollIntoView({ behavior: 'smooth', block: b });
                
                this.$vuetify.goTo(photoElement, {
                    container: this.$parent.$parent.$parent,
                    duration: 500,
                    offset: 0,
                    easing: 'easeInOutCubic',
                });
                
            },

            indexOfFirstVisiblePhoto() {
                let photoElement = null;
                let index = 0;
                for (let i=0; i<this.segment.assets.length;i++) {
                    photoElement = this.$refs['p' + i][0]
                    
                    // if (isReallyVisible(photoElement.getImgElement(), true, this.targetHeight)) {
                    if (photoElement.isVisible()) {
                        index = i
                        break;
                    }
                }
                return index;
            },
            getPhotoLength() {
                return this.segment.assets.length;
            },

            markPhoto(index, value) {
                let wallPhoto = this.$refs['p' + index][0];
                if (wallPhoto)
                    wallPhoto.mark(value);

            },
            selectPhoto(index, value) {
                let wallPhoto = this.$refs['p' + index][0];
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
                let photo = this.segment.assets[index];
                // let self = this;
                this.$store.dispatch("setRating", {photo: photo, stars: value}).then( result => {
                    this.$set(this.segment.assets, index, result);
                    this.$store.commit("setSelectedPhoto", result);
                });
            },


            // eslint-disable-next-line no-unused-vars
            
            onIntersect(entries, observer, isIntersecting) {
                if (isIntersecting) {
                    // console.log(element.target.id + " visible")
                    this.visible = true;
                    this.$emit('update-timeline', this.segment.date)
                } else {
                    this.visible = false;
                    // console.log(element.target.id + " invisible")
                }
            },
            
            resize() {
                this.contWidth = this.$refs.segmentCont.clientWidth;
            },
            thumbSrc(photo) {
                return encodeURI(this.$basePath +"/assets/preview/" + this.targetHeight + "/" + photo.path);
            },

            clickPhoto(index) {
                this.$emit("click-photo", this, index)
            },
            getFirstPhoto() {
                return this.segment.assets[0];
            },

            getLastPhoto() {
                return this.segment.assets[this.segment.assets.length-1];
            },
            clickLastPhoto() {
                this.clickPhoto( this.segment.assets.length-1);
            }


        }
    }
</script>
<style scoped>
    .segment {
        display: flex;
        flex-wrap: wrap;   
        margin-right: 64px;
    }

    .segment::after {
        content: '';
        flex-grow: 1e4;
        min-width: 20%;
      }
</style>