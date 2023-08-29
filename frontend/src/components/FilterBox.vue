/*
 * Copyright (C) 2023 Sergii Puliaiev
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
    <v-card flat class="filtersBox">
        <v-card-title>
            <v-container class="d-flex child-flex col filters">
                <v-row dense class="bg-green">
                    <v-col cols="1" class="v-col-1">
                        Filters 
                    </v-col>
                    <v-col class="v-col-auto float-left">
                        <v-btn @click="applyFilters" text color="primary" style="float: inline-end;">
                            Apply
                            <v-icon right>mdi-filter</v-icon>
                        </v-btn>
                    </v-col>
                </v-row>
            </v-container>
        </v-card-title>
        <v-card-text>
            <v-container class="d-flex child-flex col filters">
                <v-row dense class="bg-green">
                    <v-col cols="2" class="v-col-2" v-if="showPersonFilter">
                        Name:
                        <v-combobox :search-input.sync="person_name"
                                    :items="knownPersons"
                                    item-text="name"
                                    item-value="id"                                                
                                    v-model="person">                                                                                                            
                        </v-combobox>
                    </v-col>
                    <v-col cols="2" class="v-col-2" v-if="showConfidenceFilter">
                        Confidence Level:
                        <v-switch
                            color="warning"
                            v-model="switchNone"
                            label="None">
                            <v-icon color="warning" >mdi-eye-circle</v-icon>
                        </v-switch>
                        <v-switch
                            color="info"
                            v-model="switchMayBe"
                            label="Maybe">
                            <v-icon color="warning" >mdi-help-circle</v-icon>
                        </v-switch>
                        <v-switch
                            color="info"
                            v-model="switchSafe"
                            label="Safe">
                            <v-icon color="info" >mdi-leaf-circle</v-icon>
                        </v-switch>
                        <v-switch
                            color="info"
                            v-model="switchVerySafe"
                            label="Very safe">
                            <v-icon color="info" >mdi-star-circle</v-icon>
                        </v-switch>
                        <v-switch
                            color="success"
                            v-model="switchConfirmed"
                            label="Confirmed">
                            <v-icon color="info" >mdi-check-circle</v-icon>
                        </v-switch>
                    </v-col>
                    <v-col class="v-col-auto float-left">
                    </v-col>
                </v-row>
            </v-container>
        </v-card-text>
    </v-card>
</template>
<script>
    import { mapState } from 'vuex'

    export default {
        
        name: "FilterBox",
        props: {
            knownPersons: Array,
            showPersonFilter: Boolean,
            showConfidenceFilter: Boolean
        },

        data() {
            return {
                person: null,
                person_id: null,
                person_name: null,
                switchNone: true,
                switchMayBe: true,
                switchSafe: true,
                switchVerySafe: true,
                switchConfirmed: true,
            }
        },
        mounted() {
           /*
           this.$store.dispatch("getClosestPerson", this.face).then(result => {
                this.closestPerson = result.person;
                this.distance = result.distance;
            });
            */
        },
        computed: {
            ...mapState({
            }),

        },
        watch: {},
        methods: {
            applyFilters() {
                let filters = {};
                if (this.showPersonFilter && this.person) {
                    if (this.person.id) {
                        filters.person_id = this.person.id;
                    } else {
                        filters.person_name = this.person;
                    }
                }
                if (this.showConfidenceFilter) {
                    filters.switchNone = this.switchNone;
                    filters.switchMayBe = this.switchMayBe;
                    filters.switchSafe = this.switchSafe;
                    filters.switchVerySafe = this.switchVerySafe;
                    filters.switchConfirmed = this.switchConfirmed;
                }
                this.$emit("applyFilters", filters)
            },

        }
    }
</script>

<style scoped>
.filtersBox {
    border: 1px solid #D0D0D0;
    border-radius: 10px;
}
</style>
