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
    <div>
        <div v-text="date" class="caption" style="position: absolute; left: -10px; top: -0.75em"></div>
        <div v-for="t in ticks"
             :style="{
                position:'absolute',
                top:t + 'px',
                'width':'10px',
                'height':'2px',
                'left':'20px',
                'background-color':'#a5a5a5',
                }"
             :key="t"></div>
    </div>
</template>

<script>

    export default {
        name: "Tick",

         data() {
             return {
                 height: 0,
             }
         },
        mounted() {
        },

       props: {
            moment: Object,
            h: Number
        },
        computed: {

            date() {
                let result = "";
                if (this.moment.date() === 1 && this.moment.month() === 0)
                    result =  this.moment.format("YYYY")
                
                // else
                //    result = this.moment.format("MMM-YY")
                
                return result;
            },
            ticks() {
                let result = [];
                const distance = 15;
                const count = Math.floor(this.h / distance);
                const real_dist = this.h / count
                console.log(count);
                let pos = 0;
                for (let i=0; i<count; i++) {
                    result.push(pos);
                    pos += real_dist
                }
                return result;
            }
        },
    }
</script>

<style scoped>
</style>