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
    <v-container fluid class="fill-height">
        <v-row now-gutters class="fill-height">
            <v-col class="noscroll" ref="wall" >
                    <v-sheet class="scroller ma-2" tabindex="0" 
                            ref="scroller" 
                            @mousedown="clearNav()"
                            @keydown="keyboardActionWall($event)">

                            <div v-if="showPhotoCount" class="ma-2 text-h2">{{totalPhotos}} Photos</div>

                            <photo-section
                                    v-for="section in sections"
                                    :ref="'section' + section.id"
                                    :section="section"
                                    :target-height="previewHeight"
                                    :key="section.uuid"
                                    :initial-height="height(section)"
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
                            </photo-section>
                        </v-sheet>
            </v-col>
                <v-card class="noscroll scale" ref="timelineContainer" elevation="0"
                        v-on:mousemove="calcPosition($event)"
                        v-on:mouseenter="scrub(true)"
                        v-on:mouseleave="scrub(false)"
                        v-on:click="jumpToDate()">
                    <div v-for="(d, index) in tickDates" :key="index" :style="{top:pos_percent(d) + '%',position:'absolute'}" >
                        <tick v-if="showTick[index]" :moment="d" :h="tickHeight[index]"></tick>
                    </div>
                    <div id="tick" :style="cssProps"></div>
                    <div v-if="scrubbing" id="currentDate" :style="cssProps">{{currDate}}</div>
                </v-card>
        </v-row>
        
        <v-dialog
            v-model="photoFullscreen"
            fullscreen hide-overlay
            @keydown="keyboardActionDialog($event)"
            ref="viewerDialog">
            <image-viewer :photo="currentPhoto" ref="viewer"
                            :nextPhoto="nextPhoto"
                            :prevPhoto="prevPhoto"
                            :direction="imageViewerDirection"
                            @close="photoFullscreen = false"
                            @set-rating="setRating"
                            @left="navigate(-1)"
                            @right="navigate(1)"
                            >

            </image-viewer>
        </v-dialog>

    </v-container>
</template>

<script>

    /* Todo: Unify curentSelettion, segment ... and selectedSegment, section .... This is complicated and not necessary */

    import axios from "axios";
    import PhotoSection from "./PhotoSection";
    import ImageViewer from "./ImageViewer";
    import moment from "moment"
    import Tick from "./Tick";
    import { mapState } from 'vuex'

    const logBase = (n, base) => Math.log(n) / Math.log(base);
    export default {
        name: "PhotoWall",

        components: {
            PhotoSection,
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
                // for navigation and selection
                currentSegment: null,
                currentSection: null,
                currentIndex: -1,
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
                totalPhotos: 0,
                prevPhoto: null,
                nextPhoto: null,
                imageViewerDirection: 0,
                selectMulti: false,
                showTick: [],
                tickHeight: []
            };
        },

        mounted() {
            // this.viewportWidth = this.$refs.wall.clientWidth;
            if (!this.sections || this.sections.length == 0)
                this.loadAllSections();
            
            
            this.$nextTick(function() {
                this.$refs.scroller.$el.focus();
            });
            
            this.$emit("set-goback", null);
            this.$store.commit("setSelectionAllowed", this.selectionAllowed);
            this.lastTickYPos = Number.MAX_VALUE;
        },

        watch: {
            /*
            sections(val) {
                if (val.length > 0) {
                    this.currentSection = this.getNextSection(0, 0);
                    this.currentSegment = this.currentSection.getFirstSegment();
                    this.currentIndex = 0;
                    this.currentPhoto = this.currentSegment.data.photos[0];
                }

            }*/
            tick_visible() {
                this.lastTickYPos = this.currentTickYPos;
            }
        },

        computed: {

            ...mapState({
                /*
                markMode: state => state.person.markMode,
                */
                previewHeight: state => state.person.previewHeight,
                /*
                selectedSegment: state => state.photo.selectedSegment,
                selectedSection: state => state.photo.selectedSection,
                selectedIndex: state => state.photo.selectedIndex,
                selectedPhoto: state => state.photo.selectedPhoto,
                */
                selectedPhotos: state => state.photo.selectedPhotos
                
            }),
            cssProps() {
                return {
                    '--current-tick': this.currentTick + "px",
                    '--current-tick-text': (this.currentTick - 10) + 'px',
                    '--tick-color': this.$vuetify.theme.secondary
                }
            },

            tick_visible() {
                return this.currentTickYPos > this.lastTickYPos > 20; 
            }
        },

         // eslint-disable-next-line no-unused-vars
        beforeRouteLeave(to, from, next) {
            this.$store.commit("emptySelectedPhotos");
            next();
        },
        methods: {

            // eslint-disable-next-line no-unused-vars
            /*
            onIntersect(entries, observer) {
                let element = entries[0];
                console.log(element.isIntersecting)
            },     
            */
            calcTickPositions() {
                this.tickDates = this.getTickDates();
                let currentTickYPos = 0;
                let lastTickYPos = Number.MIN_SAFE_INTEGER;
                
                for (let index=0; index<this.tickDates.length-1; index++) {
                    let top = this.tickDates[index];
                    let bottom = this.tickDates[index+1];

                    let start_pos = this.pos_percent(top);
                    let end_pos = this.pos_percent(bottom);

                    let nextTickYPos = start_pos/100 * this.$refs.timelineContainer.$el.clientHeight;
                    if (nextTickYPos - lastTickYPos > 30) {
                        lastTickYPos = currentTickYPos;
                        this.showTick[index] = true;
                    } else {
                        this.showTick[index] = false;
                    }
                    currentTickYPos = nextTickYPos;
                    
                    let h = (end_pos -  start_pos)/100 * this.$refs.timelineContainer.$el.clientHeight;
                    this.tickHeight[index] = h;
                }
            },
            /*
            tick_height(tick_index) {

                if (tick_index+1>this.tickDates.length)
                    return 0;

                let top = this.tickDates[tick_index];
                let bottom = this.tickDates[tick_index+1];

                let start_pos = this.pos_percent(top);
                let end_pos = this.pos_percent(bottom);
                this.currentTickYPos = start_pos/100 * this.$refs.timelineContainer.$el.clientHeight;
                let h = (end_pos -  start_pos)/100 * this.$refs.timelineContainer.$el.clientHeight;
                return h;
            },
            */
            getTickDates() {
                // let start = moment(this.max_date);
                // let end = moment(this.min_date);
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
                this.currentTick = p * this.$refs.timelineContainer.$el.clientHeight;
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
                    let sectionEl = sectionRef.$el;
                    if (sectionEl) {
                        sectionEl.scrollIntoView();
                    }

                });

            },

            getDateByPosition(y) {
                let pos = y / this.$refs.timelineContainer.$el.clientHeight;
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

                while (target != this.$refs.timelineContainer.$el) {
                    this.currentTick += target.offsetTop;
                    target = target.offsetParent;
                }
                let selectedDate = this.getDateByPosition(this.currentTick);
                this.currDate = selectedDate.format("MMM-YYYY")
                /* eslint-disable no-console */
                // console.log(event);
            },

            
            pos_percent_log(d) {
                let duration = moment.duration(this.max_date.diff(d));
                let durationAsDays = duration.asDays();
                if (durationAsDays == 0)
                    return 0;
                let lv = logBase(durationAsDays, this.total_duration.asDays());
                return lv * 100;
            },

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
                let p = segment.data.photos[index]
                if (value) {
                    this.$store.commit("setSelectionBoundaries", {section:section.id, segment:segment.data.nr, index:index} );
                    if (this.selectMulti) {
                        let lowerBoundary = this.$store.state.photo.lowerSelectionBound;
                        let startSection = this.$refs['section' + lowerBoundary.section][0];
                        let startSegment = startSection.getSegmentEl(lowerBoundary.segment);
                        let photoIndex = lowerBoundary.index;
                        while (this.isBefore(startSection.section, startSegment.data, photoIndex, section, segment.data, index)) {
                            let p = startSegment.data.photos[photoIndex];
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
                    while (this.isBefore(startSection.section, startSegment.data, photoIndex, endSection.section, endSegment.data, endIndex)) {
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
                this.currentSection = this.$refs['section' + section.id][0];
                this.currentSegment = segment;
                this.currentIndex = photoIndex;
                this.currentPhoto = segment.data.photos[photoIndex]
                this.prevPhoto = this.getNextPhotoNewAA(this.currentSection, this.currentSegment, this.currentIndex, -1);
                this.nextPhoto = this.getNextPhotoNewAA(this.currentSection, this.currentSegment, this.currentIndex, 1);

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
                    this.setRating(value, this.currentSegment, this.currentIndex);
                }
            },

            keyboardActionDialog(event) {
                // are these values somewhere defined as constants?
                /*
                if (event.code == "ArrowLeft")
                    this.advancePhoto(-1);
                else if (event.code == "ArrowRight")
                    this.advancePhoto(1);
                else if (event.code.startsWith("Digit")) {
                    let value = parseInt(event.key);
                    this.setRating(value, this.selectedSegment, this.selectedIndex);
                }
                */
                if (event.code == "ArrowLeft")
                    this.navigate(-1);
                else if (event.code == "ArrowRight")
                    this.navigate(1);
                else if (event.code.startsWith("Digit")) {
                    let value = parseInt(event.key);
                    this.setRating(value, this.currentSegment, this.currentIndex);
                }

            },
            clearNav() {
                if (this.currentSegment) {
                    this.currentSegment.markPhoto(this.currentIndex, false);
                    this.currentIndex = -1;
                }
                this.$store.commit("markMode", false);

            },

            findFirstVisibleSegment() {

                let sectionElement = null;
                /*
                for (let i=0; i<this.sections.length; i++) {
                    sectionElement = this.$refs['section' + i][0];
                    if (sectionElement && sectionElement.isVisible())
                        break;
                }
                */
               
                this.sections.some(section => {
                    sectionElement = this.$refs['section' + section.id][0];
                    if (sectionElement.isVisible())
                        return sectionElement

                });
                
                if (sectionElement) {
                    // now we have the first visible section
                    // let's find the fist visible segment
                    this.currentSection = sectionElement;
                    this.currentSegment = this.currentSection.findFirstVisibleSegment();
                    this.currentIndex = this.currentSegment.indexOfFirstVisiblePhoto();
                }
                
            },
            scrollToMarkedPhoto(dir) {
                if (this.currentSegment && this.currentSegment.isVisible() && 
                    this.currentIndex >= 0 && this.currentSegment.photoIsVisible(this.currentIndex)) 
                    // we are still in the same area, so no change here
                    return;
                this.currentSegment.scrollToPhoto(this.currentIndex, dir)
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

            nextNonEmptySection(dir) {
                // let start = this.currentSection.section.id + dir;
                /*
                let el = this.$refs['section' + start];
                while (!el || (el && !el[0])) {
                    start += dir;
                    el = this.$refs['section' + start];
                }
                */
                let newSection = this.getNextSection(this.currentSection.section.id, dir)
                if (newSection.section.id != this.currentSection.section.id) {
                    // otherwise we are either at the beginning or the end, in any case nothing to do
                    this.currentSection = newSection;
                    if (dir == 1) {
                        this.currentSegment = this.currentSection.getFirstSegment();
                        this.currentIndex = 0;
                    } else {
                        this.currentSegment = this.currentSection.getLastSegment();
                        this.currentIndex = this.currentSegment.getPhotoLength()-1;
                    }
                } else {
                    if (dir == 1) {
                        this.currentSegment = this.currentSection.getLastSegment();
                        this.currentIndex = this.currentSegment.getPhotoLength()-1;
                    } else {
                        this.currentSegment = this.currentSection.getFirstSegment();
                        this.currentIndex = 0;
                    }
                }
            },

            selectPhoto() {
                if (this.currentIndex != -1) {
                    let p = this.currentSegment.data.photos[this.currentIndex];
                    let alreadySelected = this.selectedPhotos.some(photo => photo.id == p.id);
                    if (alreadySelected) {
                        this.$store.commit("removePhotoFromSelection", p);
                        this.currentSegment.selectPhoto(this.currentIndex, false);
                    } else {
                        this.$store.commit("addPhotoToSelection", p);
                        this.currentSegment.selectPhoto(this.currentIndex, true);
                    }

                }
            },

            navigate(dir) {
                // this.$store.commit("markMode", true);
                this.imageViewerDirection = dir;
                if (!this.currentSection || !this.currentSegment || !this.currentPhoto) {
                    this.currentSection = this.getNextSection(0, 0);
                    this.currentSegment = this.currentSection.getFirstSegment();
                    this.currentIndex = -1;
                    this.currentPhoto = this.currentSegment.data.photos[0];

                } else {
                    if (dir == 1) {
                        this.prevPhoto = this.currentPhoto; 
                        this.currentPhoto = this.nextPhoto;
                        this.nextPhoto = this.getNextPhotoNewAA(this.currentSection, this.currentSegment, this.currentIndex, dir*2);
                    } else {
                        this.nextPhoto = this.currentPhoto;
                        this.currentPhoto = this.prevPhoto;
                        this.prevPhoto = this.getNextPhotoNewAA(this.currentSection, this.currentSegment, this.currentIndex, dir*2);
                    }
                }
                if (this.currentIndex == -1) {
                    this.findFirstVisibleSegment();
                    this.currentSegment.markPhoto(this.currentIndex, true);
                } else {

                    if (this.currentSegment && this.currentIndex >= 0)
                        this.currentSegment.markPhoto(this.currentIndex, false);

                    this.currentIndex += dir;
                    if (! this.currentSegment) {
                        this.currentSection = this.$refs.section0[0]
                        this.currentSegment = this.currentSection.getFirstSegment()
                    }

                    if (this.currentIndex < 0 || this.currentIndex >= this.currentSegment.data.photos.length) {

                        this.currentSegment = this.currentSection.nextSegment(this.currentSegment, dir);

                        if (this.currentSegment) {
                            if (dir == 1)
                                this.currentIndex = 0;
                            else 
                                this.currentIndex = this.currentSegment.getPhotoLength()-1;
                        } else {
                            // next or previous photo is not in the current section, so go one section ahead or back
                            this.nextNonEmptySection(dir);

                        }
                    }
                }
                if (this.currentSegment) {
                    this.scrollToMarkedPhoto(dir);
                    this.currentSegment.markPhoto(this.currentIndex, true);
                    this.currentPhoto = this.currentSegment.data.photos[this.currentIndex];
                } else
                    this.currentIndex = -1;

            },

            
            getNextSectionSegmentAndPhoto(sectionElement, segment, index, dir) {
                let nextPhoto = null;
                let nextSection = sectionElement;
                let nextSegment = segment;
                let nextIndex = index + dir;
                if (nextIndex >= 0 && nextIndex < segment.data.photos.length) {
                    nextPhoto = segment.data.photos[index-1];
                } else {
                    // Photo is in next segment or next section
                    // first go for next segment in same section
                    // let el = this.$refs['section' + sectionElement.section.id][0];
                    // let nextSegment = el.advanceSegment(segment, dir)
                    nextSegment = sectionElement.nextSegment(segment, dir)
                    if (! nextSegment) {
                        nextSection = this.getNextSection(sectionElement.section.id, dir);
                        nextSegment = this.getNextSegment(nextSection, dir);
                    }
                    if (dir == 1) {
                        nextPhoto = nextSegment.getFirstPhoto();
                        nextIndex = 0;
                    } else {
                        nextPhoto = nextSegment.getLastPhoto();
                        nextIndex = nextSegment.data.photos.length;
                    }

                }
                return {section:nextSection, segment:nextSegment, index:nextIndex, photo: nextPhoto };
            },
            
            getLastSectionIndex() {
                let lastSection = this.sections[this.sections.length-1]
                return lastSection.id
            },
            getNextSection(sectionIndex, dir) {
                let next_section_id = sectionIndex + dir;
                if (next_section_id < 0 || next_section_id > this.getLastSectionIndex())
                    return this.$refs['section' + sectionIndex][0]

                let el = this.$refs['section' + next_section_id]
                while (!el || (el && !el[0])) {
                    next_section_id += dir;
                    el = this.$refs['section' + next_section_id]
                }
                return el[0];
            },

            getNextSegment(section, dir) {
                let nextSegment = null;
                if (dir == 1)
                    nextSegment = section.getFirstSegment()
                else
                    nextSegment = section.getLastSegment();
                return nextSegment;
            },
            
            findNextSegment(section, dir) {
                let nextSection = this.getNextSection(section, dir);
                let nextSegment = this.getNextSegment(nextSection, dir);
                return nextSegment;
            },
            /*
            getNextSegment(dir) {
                let nextSegment = null;
                let next_section_id = this.selectedSection.id + dir;
                let el = this.$refs['section' + next_section_id]
                while (el && !el[0]) {
                    next_section_id += dir;
                    el = this.$refs['section' + next_section_id]
                }
                if (dir == 1)
                    nextSegment = el[0].getFirstSegment()
                else
                    nextSegment = el[0].getLastSegment();
                return nextSegment;
            },
            */
            getNextPhotoNewAA(sectionElement, segment, index, dir) {
                let nextPhoto = null;
                let nextIndex = index + dir;
                    
                if (nextIndex >= 0 && nextIndex < segment.data.photos.length) {
                    nextPhoto = segment.data.photos[nextIndex];
                } else {
                    // Photo is in next segment or next section
                    // first go for next segment in same section
                    //  let nextSegment = this.getNextSegment(section, dir)
                    let nextSegment = sectionElement.nextSegment(segment, dir);
                    if (!nextSegment) {
                        nextSegment = this.findNextSegment(sectionElement.section.id, dir)
                    } 
                    if (nextSegment)
                        if (dir == 1)
                            nextPhoto = nextSegment.getFirstPhoto();
                        else
                            nextPhoto = nextSegment.getLastPhoto();

                }
                return nextPhoto;
            
            },
            /*
            getNextPhoto(index, dir) {
                let nextPhoto = null;
                let nextIndex = index;
                    
                if (nextIndex >= 0 && nextIndex <= this.selectedSegment.data.photos.length) {
                    nextPhoto = this.selectedSegment.data.photos[nextIndex-1];
                } else {
                    // Photo is in next segment or next section
                    // first go for next segment in same section
                    let el = this.$refs['section' + this.selectedSection.id][0];
                    let nextSegment = el.advanceSegment(this.selectedSegment, dir)
                    if (! nextSegment) {
                       nextSegment = this.findNextSegment(this.selectedSegment, dir);
                    }
                    if (nextSegment)
                        if (dir == 1)
                            nextPhoto = nextSegment.getFirstPhoto();
                        else
                            nextPhoto = nextSegment.getLastPhoto();

                }
                return nextPhoto;
            },
            */
            /*
            advancePhoto: function (dir) {
                this.$store.commit("navigate", dir);
                // this.selectedIndex += dir;
                this.imageViewerDirection = dir;

                if (dir == 1) {
                    this.prevPhoto = this.selectedPhoto; 
                    this.nextPhoto = this.getNextPhoto(this.selectedIndex, dir);
                } else {
                    this.prevPhoto = this.getNextPhoto(this.selectedIndex, dir);
                    this.nextPhoto = this.selectedPhoto;
                }


                if (this.selectedIndex >= 0 && this.selectedIndex  < this.selectedSegment.data.photos.length) {
                    this.$store.commit("setSelectedPhoto",this.selectedSegment.data.photos[this.selectedIndex]);
                    // this.selectedPhoto = this.selectedSegment.data.photos[this.selectedIndex];
                } else {
                    // Photo is in next segment or next section
                    // first go for next segment in same section
                    let el = this.$refs['section' + this.selectedSection.id][0];
                    this.$store.commit("setSelectedSegment", el.advanceSegment(this.selectedSegment, dir));
                    // this.selectedSegment = el.advanceSegment(this.selectedSegment, dir)
                    if (! this.selectedSegment) {
                        // next or previous photo is not in the current section, so go one section ahead or back
                        let next_section_id = this.selectedSection.id + dir;
                        if (next_section_id >= 0 && next_section_id < this.sections.length) {
                            // find vue component holding the next/prev section
                            el = this.$refs['section' + next_section_id][0];
                            if (dir == 1)
                                el.clickFirstPhoto();
                            else
                                el.clickLastPhoto();
                        } else {
                            // we are at the beginning
                            // reset everything
                            this.$store.commit("setSelectedIndex", 0);
                            this.$store.commit("setSelectedSegment", el.getFirstSegment());
                        }


                    }

                }
                
            },
            */
            height(section) {
                const unwrappedWidth = (3 / 2) * section.num_photos * this.previewHeight * (7 / 10);
                const rows = Math.ceil(unwrappedWidth / this.$refs.wall.clientWidth);
                // const rows = Math.ceil(unwrappedWidth / this.$refs.wall.clientWidth);
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
                    this.totalPhotos = result.data.totalPhotos;
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

    .scale {
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
