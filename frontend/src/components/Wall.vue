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
    <v-container ref="wall" fluid class="fill-height">
        <v-row class="fill-height">
            <v-col class="noscroll ma-2">
                <v-sheet class="scroller" 
                    tabindex="0"
                    @mousedown="clearNav()"
                    @keydown="keyboardActionWall($event)">
                
                <div class="mt-2 text-h3">{{totalAssets}} Photos/Videos</div>
                    <asset-section v-for="section in sections"  
                        :ref="'section' + section.id"
                        :target-height="previewHeight"
                        :section="section"
                        :key="section.id"
                        :initialHeight="height(section)"
                        :filter-person-id="personId"
                        :filter-thing-id="thingId"
                        :filter-album-id="albumId"
                        :city="city"
                        :county="county"
                        :country="country"
                        :state="state"
                        :from="from"
                        :to="to"
                        :camera="camera"
                        :rating="rating"
                        @click-photo="clickPhoto"
                        @select-photo="selectPhotoEvent"
                        @select-multi="selectMultiEvent"
                        @update-timeline="updateTimeline">
                    </asset-section>
                    
                </v-sheet>
            </v-col>
            
            <div class="noscroll timelineContainer ma-2" 
                ref="timelineContainer"
                v-on:mousemove="calcPosition($event)"
                v-on:mouseenter="scrubbing = true"
                v-on:mouseleave="scrubbing = false"
                v-on:click="jumpToDate()">
                <div v-for="(tick, index) in ticks" :key="index" 
                    :style="{top:tick.pos + 'px',height:tick.height + 'px', position:'absolute', width:'30px'}" >
                    <div style="position: relative">
                        <tick :moment="tick.date" :h="tick.height"></tick>
                    </div>
                </div>
                <div id="tick" :style="cssProps"></div>
                <div v-if="scrubbing" id="currentDate" :style="cssProps">{{currDate}}</div>
            </div>
        
        </v-row>
        
        <v-dialog
            v-model="photoFullscreen"
            fullscreen hide-overlay
            @keydown="keyboardActionDialog($event)"
            ref="viewerDialog">
            <image-viewer :photo="currentPhoto.asset" ref="viewer"
                            :nextPhoto="nextPhoto.asset"
                            v-if="photoFullscreen"
                            :prevPhoto="prevPhoto.asset"
                            :direction="imageViewerDirection"
                            @close="closeViewer"
                            @set-rating="setRating"
                            @left="navigate(-1)"
                            @right="navigate(1)">
            </image-viewer>
        </v-dialog>
        
    </v-container>
 </template>

<script>
    import axios from "axios";
    import AssetSection from "./AssetSection";
    import ImageViewer from "./ImageViewer";
    import moment from "moment"
    import Tick from "./Tick"; 
    import { mapState } from 'vuex'

    // const logBase = (n, base) => Math.log(n) / Math.log(base);
    
    export default {
        name: "Wall",

        components: {
            AssetSection,
            ImageViewer,
            Tick
        },

        props: {
            personId: Number,
            thingId: String,
            city: String,
            county: String,
            country: String,
            state: String,
            from: String,
            to: String,
            rating: Number,
            camera: String,
            albumId: Number,
            showPhotoCount: {
                type: Boolean,
                default: true
            },
            selectionAllowed: {
                type: Boolean,
                default: true
            }
        },
        data() { 
            return {
                photoFullscreen: false,
                currentPhoto: null,
                // ---
                sections: [],
                min_date: null,
                max_date: null,
                total_scale: null,
                currentTick: 0,
                lastTickYPos: 0,
                currentTickYPos: 0,
                currDate: "",
                scrubbing: false,
                tickDates: [],
                totalAssets: 0,
                prevPhoto: null,
                nextPhoto: null,
                imageViewerDirection: 0,
                selectMulti: false,
                ticks: [],
            };
        },

        mounted() {
            if (!this.sections || this.sections.length == 0)
                this.loadAllSections();            
            this.$emit("set-goback", null);
            this.$store.commit("setSelectionAllowed", this.selectionAllowed);
            this.lastTickYPos = Number.MAX_VALUE;
        },

        watch: {
        },

        computed: {

            ...mapState({
                previewHeight: state => state.person.previewHeight,
                selectedPhotos: state => state.photo.selectedPhotos
                
            }),
            cssProps() {
                return {
                    '--current-tick': this.currentTick + "px",
                    '--current-tick-text': (this.currentTick - 10) + 'px',
                    '--tick-color': this.$vuetify.theme.secondary
                }
            },
        },

         // eslint-disable-next-line no-unused-vars
        beforeRouteLeave(to, from, next) {
            this.$store.commit("emptySelectedPhotos");
            next();
        },

        methods: {
            
            closeViewer() {
                this.photoFullscreen = false;
                this.currentPhoto = null;
            },
            calcTickPositions() {
                this.tickDates = this.getTickDates();
                for (let index=0; index<this.tickDates.length-1; index++) {
                    const top = this.tickDates[index];
                    const bottom = this.tickDates[index+1];

                    const start_pos = this.pos_percent(top);
                    const end_pos = this.pos_percent(bottom);

                    const startTickYPos = start_pos/100 * this.$refs.timelineContainer.clientHeight;
                    const endTickYPos = end_pos/100 * this.$refs.timelineContainer.clientHeight;
                    const height = endTickYPos - startTickYPos

                    if (height > 30) {
                        const tick = {
                            pos: startTickYPos,
                            height: height,
                            date: this.tickDates[index]
                        };
                        this.ticks.push(tick);
                    } 
                }
            },

            getTickDates() {
                let result = [];

                if (this.max_date || this.min_date) {
                    let init = moment(this.max_date);
                    result.push(init);
                    let start = moment(init).startOf("year");

                    for (let m = start; m.isAfter(this.min_date); m.add(-1, 'years')) {
                        let mc = moment(m);
                        result.push(mc);
                    }

                    let exit = moment(this.min_date);
                    result.push(exit);
                }
                return result;
            },

            updateTimeline(currentDate) {
                let m = moment(currentDate);
                this.currDate = m.format("MMM-YYYY");
                let p = this.pos_percent(m)/100;
                this.currentTick = p * this.$refs.timelineContainer.clientHeight;
            },

            findSectionForDate(date) {
                axios.get("/api//section/find_by_date/" + date ).then((result) => {
                    self.sections = result.data;
                });

            },

            jumpToDate() {
                let selectedDate = this.getDateByPosition(this.currentTick);
                let self = this;
                axios.get("/api/section/find_by_date/" + selectedDate.format("YYYY-MM-DD") ).then((result) => {
                    let sectionId = result.data;
                    let sectionRef = self.$refs['section' + sectionId][0];
                    // let sectionEl = sectionRef.$el;
                    // console.log(sectionEl);
                    sectionRef.scrollTo(selectedDate)

                });

            },

            getDateByPosition(y) {
                let pos = y / this.$refs.timelineContainer.clientHeight;
                let total_days = this.total_duration.asDays();
                // let positionsOfDay = Math.pow(total_days, pos);
                // let positionsOfDay = Math.cos( (this.total_duration.asDays() - durationAsDays) / this.total_duration.asDays()  * Math.PI/2)
                let mc = Math.acos( pos );
                let positionsOfDay = mc/ (Math.PI/2) * total_days;
                let selectedDate = moment(this.min_date);

                selectedDate.add(positionsOfDay, "days");
                return selectedDate;
            },
            scrub(v) {
                this.scrubbing = v;
            },

            calcPosition(event) {

                if (! this.total_duration)
                    return;

                let target = event.target;
                this.currentTick = event.offsetY;
                // console.log(target);
                while (target != this.$refs.timelineContainer) {
                    this.currentTick += target.offsetTop;
                    target = target.offsetParent;
                }
            
                let selectedDate = this.getDateByPosition(this.currentTick);
                this.currDate = selectedDate.format("MMM-YYYY")
                /* eslint-disable no-console */
                // console.log(event);
            },

            /*
            pos_percent_log(d) {
                let duration = moment.duration(this.max_date.diff(d));
                let durationAsDays = duration.asDays();
                if (durationAsDays == 0)
                    return 0;
                let lv = logBase(durationAsDays, this.total_duration.asDays());
                return lv * 100;
            },
            */
            pos_percent(d) {
                let duration = moment.duration(this.max_date.diff(d));
                let durationAsDays = duration.asDays();
                if (durationAsDays == 0)
                    return 0;
                let lv = Math.cos( (this.total_duration.asDays() - durationAsDays) / this.total_duration.asDays()  * (Math.PI/2))
                return lv * 100;
            },

            isBefore(sectionA, segmentA, indexA, sectionB, segmentB, indexB) {
                return  (sectionA.id < sectionB.id) ||
                        (sectionA.id == sectionB.id && segmentA.nr < segmentB.nr) ||
                        (sectionA.id == sectionB.id && segmentA.nr == segmentB.nr && indexA <= indexB);
            },
            selectPhotoEvent(section, segment, index, value) {
                let p = segment.segment.assets[index]
                if (value) {
                    this.$store.commit("setSelectionBoundaries", {section:section.id, segment:segment.segment.nr, index:index} );
                    if (this.selectMulti) {
                        let lowerBoundary = this.$store.state.photo.lowerSelectionBound;
                        let startSection = this.$refs['section' + lowerBoundary.section][0];
                        let startSegment = startSection.getSegmentEl(lowerBoundary.segment);
                        let photoIndex = lowerBoundary.index;
                        while (this.isBefore(startSection.section, startSegment.segment, photoIndex, section, segment.segment, index)) {
                            let p = startSegment.segment.assets[photoIndex];
                            this.$store.commit("addPhotoToSelection", p);
                            startSegment.selectPhoto(photoIndex, true);
                            let next = this.getNextSectionSegmentAndPhoto(startSection, startSegment, photoIndex, 1)
                            startSection = next.section;
                            startSegment = next.segment;
                            photoIndex = next.index;
                            
                        }
                        this.selectMulti = false;
                    } else {
                        this.$store.commit("addPhotoToSelection", p);
                    }
                } else {
                    this.$store.commit("removePhotoFromSelection", p)
                }
                if (this.selectedPhotos.length == 1) {
                    let self = this;
                    this.$emit("set-goback", function() {
                        self.clearSelection();
                    })
                }
            },

            clearSelection() { 
                if (this.selectedPhotos.length > 0) {
                    let lowerBoundary = this.$store.state.photo.lowerSelectionBound;
                    let upperBoundary = this.$store.state.photo.upperSelectionBound;
                    let startSection = this.$refs['section' + lowerBoundary.section][0];
                    let startSegment = startSection.getSegmentEl(lowerBoundary.segment);
                    let photoIndex = lowerBoundary.index;
                    let endSection = this.$refs['section' + upperBoundary.section][0]
                    let endSegment = endSection.getSegmentEl(upperBoundary.segment);
                    let endIndex = upperBoundary.index;
                    while (this.isBefore(startSection.section, startSegment.segment, photoIndex, endSection.section, endSegment.segment, endIndex)) {
                        startSegment.selectPhoto(photoIndex, false);
                        let next = this.getNextSectionSegmentAndPhoto(startSection, startSegment, photoIndex, 1)
                        startSection = next.section;
                        startSegment = next.segment;
                        photoIndex = next.index;            
                    }
                    this.$store.commit("emptySelectedPhotos");
                    this.$emit("set-goback", null);
                }                
            },

            selectMultiEvent() {
                this.selectMulti = true;
            },

            clickPhoto(section, segment, photoIndex) {
                this.photoFullscreen = true;
                this.imageViewerDirection = 0;
                this.currentPhoto = {
                    sectionElement: this.$refs['section' + section.id][0],
                    segmentElement: segment,
                    index: photoIndex,
                    asset: segment.segment.assets[photoIndex]
                }

                this.prevPhoto = this.getNextSectionSegmentAsset(this.currentPhoto, -1);
                this.nextPhoto = this.getNextSectionSegmentAsset(this.currentPhoto,  1);

            },

            setRating(value, segment, index) {
                if (segment == null && index == null) {
                    // if this is coming from the imageviewer then it is simply the currentIndex in the currentSegment
                    segment = this.currentSegment;
                    index = this.currentIndex;
                }
                if (value <= 5 && segment && this.currentIndex >= 0) {
                     segment.setRating(index, value); 
                     if (this.photoFullscreen) 
                         this.$refs.viewer.mouseMove();
                           
                }
            },

            keyboardActionWall(event) {
                // are these values somewhere defined as constants?
            
                if (event.code == "ArrowLeft")
                    this.navigate(-1);
                else if (event.code == "ArrowRight")
                    this.navigate(1);
                else if (event.code == "Escape") {
                    this.clearNav();
                    this.clearSelection();
                } else if (event.code == "Space") {
                    this.selectPhoto();
                    event.preventDefault();
                } else if (event.code.startsWith("Digit")) {
                    let value = parseInt(event.key);
                    this.setRating(value, 
                        this.currentPhoto.currentSegment.segment, 
                        this.currentPhoto.index);
                }
            },


            keyboardActionDialog(event) {
                // are these values somewhere defined as constants?
                if (event.code == "ArrowLeft")
                    this.navigate(-1);
                else if (event.code == "ArrowRight")
                    this.navigate(1);
                else if (event.code.startsWith("Digit")) {
                    let value = parseInt(event.key);
                    this.setRating(value, 
                        this.currentPhoto.currentSegment.segment, 
                        this.currentPhoto.index);
                } else if (event.code == "Space")
                    this.currentPhoto = null;


            },

            clearNav() {
                this.markAsset(this.currentPhoto, false);
                this.$store.commit("markMode", false);
                this.currentPhoto = null;
            },

            findFirstVisibleAsset() {

                let sectionElement = null;
                let result = null;
                this.sections.some(section => {
                    sectionElement = this.$refs['section' + section.id][0];
                    if (sectionElement.isVisible())
                        return sectionElement

                });
                
                if (sectionElement) {

                    // now we have the first visible section
                    // let's find the fist visible segment

                    const segmentElement = sectionElement.findFirstVisibleSegment();
                    const index = segmentElement.indexOfFirstVisiblePhoto();
                    const asset = segmentElement.segment.assets[index];
                    result =  {
                        sectionElement: sectionElement,
                        segmentElement: segmentElement,
                        index: index,
                        asset: asset
                    };
                }
                return result;
                
            },
            scrollToMarkedPhoto() {
                
                if (this.currentPhoto.segmentElement.isVisible() && 
                    this.currentPhoto.segmentElement.photoIsVisible(this.currentPhoto.index)) 
                    // we are still in the same area, so no change here
                    return;
                this.currentPhoto.segmentElement.scrollToPhoto(this.currentPhoto.index)
            },

            currentSectionChildIndex() {
                let index = 0;
                let self = this;
                this.$children.some(child => {
                    if (child == self.currentSection)
                        return index;
                    index++;
                });
                return index;
            },

            selectPhoto() {
                if (this.currentPhoto) {

                    let p = this.currentPhoto.asset;
                    let alreadySelected = this.selectedPhotos.some(photo => photo.id == p.id);
                    if (alreadySelected) {
                        this.$store.commit("removePhotoFromSelection", p);
                        this.currentPhoto.segmentElement.selectPhoto(this.currentPhoto.index, false);
                    } else {
                        this.$store.commit("addPhotoToSelection", p);
                        this.currentPhoto.segmentElement.selectPhoto(this.currentPhoto.index, true);
                    }

                }
            },

            markAsset(asset, value) {
                if (asset)
                    asset.segmentElement.markPhoto(asset.index, value);
            },

            navigate(dir) {
                this.imageViewerDirection = dir;
                if (!this.currentPhoto) {
                    this.currentPhoto = this.findFirstVisibleAsset();
                    this.prevPhoto = this.getNextSectionSegmentAsset(this.currentPhoto, -1);
                    this.nextPhoto = this.getNextSectionSegmentAsset(this.currentPhoto, 1);
                } else {
                    this.markAsset(this.currentPhoto, false);

                    if (dir == 1) { 
                        this.prevPhoto = this.currentPhoto; 
                        this.currentPhoto = this.nextPhoto;
                        this.nextPhoto = this.getNextSectionSegmentAsset(this.currentPhoto, 1);
                    } else {
                        this.nextPhoto = this.currentPhoto;
                        this.currentPhoto = this.prevPhoto;
                        this.prevPhoto = this.getNextSectionSegmentAsset(this.currentPhoto, -1);
                    } 

                }
                this.markAsset(this.currentPhoto, true);
                this.scrollToMarkedPhoto();

            },
            getNextSectionSegmentAndPhoto(sectionElement, segment, index, dir) {
                let nextPhoto = null;
                let nextSection = sectionElement;
                let nextSegment = segment;
                let nextIndex = index + dir;
                if (nextIndex >= 0 && nextIndex < segment.segment.assets.length) {
                    nextPhoto = segment.segment.assets[index-1];
                } else {
                    // Photo is in next segment or next section
                    // first go for next segment in same section
                    // let el = this.$refs['section' + sectionElement.section.id][0];
                    // let nextSegment = el.advanceSegment(segment, dir)
                    nextSegment = sectionElement.nextSegment(segment, dir)
                    if (! nextSegment) {
                        nextSection = this.getNextSection(sectionElement.section, dir);
                        nextSegment = this.getNextSegment(nextSection, dir);
                    }
                    if (dir == 1) {
                        nextPhoto = nextSegment.getFirstPhoto();
                        nextIndex = 0;
                    } else {
                        nextPhoto = nextSegment.getLastPhoto();
                        nextIndex = nextSegment.segment.assets.length;
                    }

                }
                return {section:nextSection, segment:nextSegment, index:nextIndex, photo: nextPhoto };
            },
            
            getLastSection() {
                return this.sections[this.sections.length-1]
            },

            getLastSectionElement() {
                return this.$refs['section' + this.sections.length][0];
            },
            
            getFirstSectionElement() {
                return this.$refs.section1[0];
            },

            isLastSectionElement(sectionElement) {
                return sectionElement == this.getLastSectionElement();
            },

            isFirstSectionElement(sectionElement) {
                return sectionElement == this.getFirstSectionElement();
            },

            getNextSection(sectionElement, dir) {
                let next_section_id = sectionElement.section.id + dir;
                if (next_section_id <= 0)
                    return this.$refs['section1'][0]

                if (next_section_id > this.sections.length)
                    return this.getLastSectionElement();

                let el = this.$refs['section' + next_section_id]
                while (!el || (el && !el[0])) {
                    next_section_id += dir;
                    el = this.$refs['section' + next_section_id]
                }
                let nextSection = el[0];
                nextSection.assertAssetsLoad();
                return nextSection;
            },

            getNextSegment(sectionElement, dir) {
                let nextSegment = null;

                if (dir == 1) 
                    nextSegment = sectionElement.getFirstSegment();
                else
                    nextSegment = sectionElement.getLastSegment();

                /*
                if (dir == 1) {
                    if (!this.isLastSectionElement(sectionElement))
                        nextSegment = sectionElement.getFirstSegment()
                    else
                        nextSegment = sectionElement.getLastSegment()
                } else {
                    if (!this.isFirstSectionElement(sectionElement))
                        nextSegment = sectionElement.getLastSegment();
                    else
                        nextSegment = sectionElement.getFirstSegment()

                }*/
                return nextSegment;
            },
            /*
            findNextSegment(sectionElement, dir) {
                let nextSection = this.getNextSection(sectionElement, dir);
                let nextSegment = this.getNextSegment(nextSection, dir);
                return nextSegment;
            },
            */
            getNextSectionSegmentAsset(currentAsset, dir) {
                let nextPhoto = currentAsset.asset;
                let nextIndex = currentAsset.index + dir;
                let nextSegmentElement = currentAsset.segmentElement;
                let nextSectionElement = currentAsset.sectionElement;

                if (nextIndex >= 0 && nextIndex < nextSegmentElement.segment.assets.length) {
                    nextPhoto = nextSegmentElement.segment.assets[nextIndex];
                } else {
                    // Photo is in next segment or next section
                    // first go for next segment in same section

                    nextSegmentElement = nextSectionElement.nextSegment(nextSegmentElement, dir);
                    if (!nextSegmentElement) {
                        // Asset is in next section
                        nextSectionElement = this.getNextSection(nextSectionElement, dir);
                        nextSegmentElement = this.getNextSegment(nextSectionElement, dir);
                    } 

                    if (dir == 1) {
                        if (nextSegmentElement != currentAsset.segmentElement) {
                            nextPhoto = nextSegmentElement.getFirstPhoto();
                            nextIndex = 0;
                        } else {
                            nextIndex = currentAsset.index 
                        }
                    } else {
                        if (nextSegmentElement != currentAsset.segmentElement) {

                            nextPhoto = nextSegmentElement.getLastPhoto();
                            nextIndex = nextSegmentElement.segment.assets.length-1; 
                        } else {
                            nextIndex = currentAsset.index 
                        }
                    }
            
                }
                return { 
                    asset: nextPhoto,
                    index: nextIndex,
                    segmentElement: nextSegmentElement,
                    sectionElement: nextSectionElement
                }
            
            },
            height(section) {
                const unwrappedWidth = (3 / 2) * section.num_assets * this.previewHeight * (7 / 10);
                const rows = Math.ceil(unwrappedWidth / this.$refs.wall.clientWidth);
                const height = rows * this.previewHeight;
                return height;
            },


            loadAllSections() {
                // let self = this;
                let params = {};
                let config = { params: params};
                if (!isNaN(this.personId))
                    params["person_id"] = this.personId;
                params["thing_id"] = this.thingId; 
                params["city"] = this.city;
                params["county"] = this.county;
                params["country"] = this.country;
                params["state"] = this.state;
                params["camera"] = this.camera;
                params["rating"] = this.rating;
                params["from"] = this.from;
                params["to"] = this.to;
                if (!isNaN(this.albumId))
                    params['album_id'] = this.albumId;
                axios.get("/api/section/all", config).then((result) => {
                    this.$set(this, "sections",  result.data.sections);
                    // this.sections = result.data.sections;
                    this.max_date = moment(result.data.max_date);
                    this.min_date = moment(result.data.min_date);
                    this.totalAssets = result.data.totalAssets;
                    this.total_duration = moment.duration(this.max_date.diff(this.min_date));
                    // this.tickDates = this.getTickDates();
                    this.calcTickPositions();
                });
            }
        }
    }
</script>

<style scoped>

    .inscroll {
        overflow: scroll;

    }
    .scroller {
        position: absolute;
        top: 0px;
        bottom: 0px;
        left: 0px;
        right: 0px;
        overflow: scroll;
        /* IE and Edge */
        /*
        -ms-overflow-style: none;  
        */
        /* Firefox */
        /*
        scrollbar-width: none;
        */  
    }
    .scroller::-webkit-scrollbar {
        display: none;
    }

    .scroller:focus {
        outline-width: 0;
    }

    .tl {
        background-color: green;
        position: absolute;
        top: 0px;
        height: 100%;
        width: 60px;
        right: 0px;
    }

    .noscroll {
        position: relative;
    }

    .timelineContainer {
        width: 30px;
    }

    #tick {
        position: absolute;
        top: var(--current-tick);
        background-color:var(--v-primary-base);
        width:20px;
        height:2px;
        left: 10px;
    }

    #currentDate {
        position: absolute;
        top: var(--current-tick-text);
        width: 80px;
        color: black;
        background-color:white;
        transform: translate(-80px, 0px);
    }

</style>
