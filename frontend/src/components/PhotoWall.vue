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
    <v-container fluid>

        <v-row no-gutters >
            <v-col ref="wall" class="noscroll">
                    <div class="scroller" tabindex="0"  
                            ref="scroller"

                            @mousedown="clearNav()"
                            @keydown="keyboardAction($event)">
                            <!--
                            @keydown.esc="clearNav()"
                            @keydown.left="navigate(-1)"
                            @keydown.right="navigate(1)"
                            -->
                        <v-card>
                            <v-card-title>{{totalPhotos}} Photos</v-card-title>
                        </v-card>

                        <photo-section
                                v-for="section in sections"
                                :ref="'section' + section.id"
                                :section="section"
                                :target-height="previewHeight"
                                :key="section.id"
                                :initial-height="height(section)"
                                :filter-person-id="personId"
                                :filter-thing-id="thingId"
                                :city="city"
                                :county="county"
                                :country="country"
                                :state="state"
                                @select-photo="selectPhoto"
                                @update-timeline="updateTimeline">
                        </photo-section>
                    </div>
            </v-col>
            <v-card class="noscroll scale" ref="timelineContainer" elevation="0"
                    v-on:mousemove="calcPosition($event)"
                    v-on:mouseenter="scrub(true)"
                    v-on:mouseleave="scrub(false)"
                    v-on:click="jumpToDate()">
                <div v-for="(d, index) in tickDates" :key="index" :style="{top:pos_percent(d) + '%',position:'absolute'}" >
                    <tick :moment="d" :h="tick_height(index)"></tick>
                </div>
                <div id="tick" :style="cssProps"></div>
                <div v-if="scrubbing" id="currentDate" :style="cssProps">{{currDate}}</div>
            </v-card>

            <v-dialog
                v-model="photoFullscreen"
                fullscreen hide-overlay
                @keydown.left="advancePhoto(-1)"
                @keydown.right="advancePhoto(1)"
                >

                <image-viewer :photo="selectedPhoto" ref="viewer"
                              @left="advancePhoto(-1)"
                              @right="advancePhoto(1)"
                              @close="photoFullscreen = false">

                </image-viewer>
        </v-dialog>
        </v-row>
    </v-container>
</template>

<script>

    import axios from "axios";
    // import moment from "moment"
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

        },
        data() {
            return {
                photoFullscreen: false,
                // for the image viewer
                selectedSegment: null,
                selectedSection: null,
                selectedIndex: 0,
                selectedPhoto: null,
                // for navigation and selection
                currentSegment: null,
                currentSection: null,
                currentIndex: -1,
                // ---
                sections: [],
                personId: this.$route.query.person_id,
                thingId: this.$route.query.thing_id,
                city: this.$route.query.city,
                county: this.$route.query.county,
                country: this.$route.query.country,
                state: this.$route.query.state,
                min_date: null,
                max_date: null,
                total_scale: null,
                currentTick: 0,
                currDate: "",
                scrubbing: false,
                tickDates: [],
                totalPhotos: 0
            };
        },

        mounted() {
            // this.viewportWidth = this.$refs.wall.clientWidth;
            if (!this.sections || this.sections.length == 0)
                this.loadAllSections();

            
            this.$nextTick(function() {
                this.$refs.scroller.focus();

            });
        },



        watch: {
        },

        computed: {

            ...mapState({
                markMode: state => state.person.markMode,
                previewHeight: state => state.person.previewHeight
            }),
            cssProps() {
                return {
                    '--current-tick': this.currentTick + "px",
                    '--current-tick-text': (this.currentTick - 10) + 'px',
                    '--tick-color': this.$vuetify.theme.secondary
                }
            },
        },
        methods: {

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
            tick_height(tick_index) {

                if (tick_index+1>this.tickDates.length)
                    return 0;

                let top = this.tickDates[tick_index];
                let bottom = this.tickDates[tick_index+1];

                let start_pos = this.pos_percent(top);
                let end_pos = this.pos_percent(bottom);

                let h = (end_pos -  start_pos)/100 * this.$refs.timelineContainer.$el.clientHeight;



                return h;
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

            selectPhoto(section, segment, photoIndex) {
                this.selectedSection = section;
                this.selectedSegment = segment;
                this.selectedIndex = photoIndex;
                this.selectedPhoto = segment.data.photos[this.selectedIndex];
                this.photoFullscreen = true;
            },

            setRating(value) {
                if (value <= 5 && this.currentSegment && this.currentIndex >= 0) {
                     this.currentSegment.setRating(this.currentIndex, value);        
                }
            },
            keyboardAction(event) {
                // are these values somewhere defined as constants?
                if (event.code == "ArrowLeft")
                    this.navigate(-1);
                else if (event.code == "ArrowRight")
                    this.navigate(1);
                else if (event.code == "Escape")
                    this.clearNav();
                else if (event.code.startsWith("Digit")) {
                    let value = parseInt(event.key);
                    this.setRating(value);
                }
            },
            clearNav() {
                if (this.currentSegment) {
                    this.currentSegment.markPhoto(this.currentIndex, false);
                    this.currentIndex = -1;
                }
                this.$store.commit("markMode", false);

            },
            findFirstVisibleSegment(dir) {

                if (this.currentSegment && this.currentSegment.isVisible() && 
                    this.currentIndex >= 0 && this.currentSegment.photoIsVisible(this.currentIndex)) {
                    // we are still in the same area, so no change here
                    this.currentIndex += dir;
                } else {
                    let sectionElement = null;
                    for (let i=0; i<this.sections.length; i++) {
                        sectionElement = this.$refs['section' + i][0];
                        if (sectionElement.isVisible())
                            break;
                    }

                    if (sectionElement) {
                        // now we have the first visible section
                        // let's find the fist visible segment
                        this.currentSection = sectionElement;
                        this.currentSegment = this.currentSection.findFirstVisibleSegment();
                        this.currentIndex = this.currentSegment.indexOfFirstVisiblePhoto();
                    }
                }
            },

            navigate(dir) {
                this.$store.commit("markMode", true);

                if (this.currentSegment && this.currentIndex >= 0)
                    this.currentSegment.markPhoto(this.currentIndex, false);

                this.findFirstVisibleSegment(dir);
                // this.currentIndex += dir;
                if (! this.currentSegment) {
                    this.currentSection = this.$refs.section0[0]
                    this.currentSegment = this.currentSection.getFirstSegment()
                }

                if (this.currentIndex < 0 || this.currentIndex >= this.currentSegment.data.photos.length) {
                    // Photo is in next segment or next section
                    // first go for next segment in same section
                    let el = this.currentSection;
                    this.currentSegment = el.nextSegment(this.currentSegment, dir);

                    if (this.currentSegment) {
                        if (dir == 1)
                            this.currentIndex = 0;
                        else 
                            this.currentIndex = this.currentSegment.getPhotoLength()-1;
                    } else {
                        // next or previous photo is not in the current section, so go one section ahead or back
                        let next_section_id = this.currentSection.id + dir;
                        if (next_section_id >= 0 && next_section_id < this.sections.length) {
                            // find vue component holding the next/prev section
                            el = this.$refs['section' + next_section_id][0];
                            if (dir == 1) {
                                this.currentSegment = el.getFirstSegment();
                                this.currentIndex = 0;
                            } else {
                                this.currentSegment = el.getLastSegment();
                                this.currentIndex = this.currentSegment.getPhotoLength();
                            }
                        }

                    }
                }
                if (this.currentSegment)
                    this.currentSegment.markPhoto(this.currentIndex, true);
                else
                    this.currentIndex = -1;

            },
            advancePhoto: function (dir) {
                this.selectedIndex += dir;

                if (this.selectedIndex >= 0 && this.selectedIndex  < this.selectedSegment.data.photos.length) {
                    this.selectedPhoto = this.selectedSegment.data.photos[this.selectedIndex];
                } else {
                    // Photo is in next segment or next section
                    // first go for next segment in same section
                    let el = this.$refs['section' + this.selectedSection.id][0];
                    this.selectedSegment = el.advanceSegment(this.selectedSegment, dir)
                    if (! this.selectedSegment) {
                        // next or previous photo is not in the current section, so go one section ahead or back
                        let next_section_id = this.selectedSection.id + dir;
                        if (next_section_id >= 0 && next_section_id < this.sections.length) {
                            // find vue component holding the next/prev section
                            el = this.$refs['section' + next_section_id][0];
                            if (dir == 1)
                                el.selectFirstPhoto();
                            else
                                el.selectLastPhoto();
                        }

                    }

                }
                
            },

            height(section) {
                const unwrappedWidth = (3 / 2) * section.num_photos * this.previewHeight * (7 / 10);
                const rows = Math.ceil(unwrappedWidth / this.$refs.wall.clientWidth);
                // const rows = Math.ceil(unwrappedWidth / this.$refs.wall.clientWidth);
                const height = rows * this.previewHeight;
                return height;
            },


            loadAllSections() {
                let self = this;
                let params = {};
                let config = { params: params};
                params["person_id"] = this.personId;
                params["thing_id"] = this.thingId; // this.$route.params.thing_id; // this.thingId;
                params["city"] = this.city;
                params["county"] = this.county;
                params["country"] = this.country;
                params["state"] = this.state;


                // eslint-disable-next-line no-console
                axios.get("/api/section/all", config).then((result) => {
                    self.sections = result.data.sections;
                    self.max_date = moment(result.data.max_date);
                    self.min_date = moment(result.data.min_date);
                    self.totalPhotos = result.data.totalPhotos;
                    self.total_duration = moment.duration(self.max_date.diff(self.min_date));
                    self.tickDates = self.getTickDates();

                });

            }

        }
    }
</script>

<style scoped>
    .scroller {
        position: absolute;
        top: 0px;
        bottom: 0px;
        left: 0px;
        right: 0px;
        overflow: auto;
        -ms-overflow-style: none;  /* IE and Edge */
        scrollbar-width: none;  /* Firefox */
    }
    .scroller::-webkit-scrollbar {
        display: none;
    }

    .scroller:focus {
        outline-width: 0;
    }
    .wallcontainer {
        position: relative;
        overflow: hidden;
        height:100%;
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
        /*  fix this */
        height: calc(100vh - 80px); 
        /* height: 100vh; */
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
