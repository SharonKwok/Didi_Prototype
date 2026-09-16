# ---------------- TAB 3: COMMUNICATIONS (Fully Redesigned per KPI Dictionary) ----------------
    with tab_comm:
        st.subheader("Communication Engagement Analytics")
        st.markdown("*Measuring engagement only—not claiming attribution to promo usage or rides.*")
        
        gov_comm = base_comm.copy()
        if not gov_comm.empty:
            st.markdown("##### 1. Communication Settings (Cascading Filters)")
            c_col1, c_col2, c_col3 = st.columns([1, 2, 2])
            
            # Filter 1: Channel (Drives the other filters)
            avail_channels = gov_comm['channel'].unique().tolist()
            comm_channel = c_col1.selectbox("1. Select Channel", ["All Channels"] + avail_channels)
            if comm_channel != "All Channels":
                gov_comm = gov_comm[gov_comm['channel'] == comm_channel]
            
            # Filter 2: Campaign (Dynamically filtered by Channel)
            # Upgraded to multiselect so user can type to search easily
            avail_campaigns = sorted(gov_comm['push_title'].unique().tolist())
            comm_campaigns = c_col2.multiselect("2. Search & Select Campaigns", avail_campaigns, default=[])
            if comm_campaigns:
                gov_comm = gov_comm[gov_comm['push_title'].isin(comm_campaigns)]
                
            # Filter 3: Step ID (Dynamically filtered by Campaign)
            if comm_campaigns:
                step_opts = gov_comm['step_id'].dropna().unique().tolist()
                step_opts = [str(int(s)) if isinstance(s, float) else str(s) for s in step_opts]
                comm_step = c_col3.multiselect("3. Select Step ID", step_opts, default=[])
                if comm_step:
                    gov_comm = gov_comm[gov_comm['step_id'].astype(str).isin(comm_step)]
            else:
                c_col3.info("👈 Select a campaign to view specific Step IDs.")

            # --- 2. Overall Communication KPIs ---
            st.markdown("---")
            st.markdown("##### 2. Overall Communication KPIs")
            total_delivered = gov_comm['delivered_count'].sum()
            total_clicks = gov_comm['clicks'].sum()
            active_campaigns = gov_comm['canvas_id'].nunique()
            del_to_click = (total_clicks / total_delivered * 100) if total_delivered > 0 else 0
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Delivered Communications", f"{total_delivered:,.0f}")
            k2.metric("Total Clicks", f"{total_clicks:,.0f}")
            k3.metric("Active Campaigns", f"{active_campaigns:,.0f}")
            k4.metric("Delivered-to-Click Rate", f"{del_to_click:.2f}%")

            # --- 3. Main Visuals & Channel Comparison ---
            st.markdown("---")
            st.markdown("##### 3. Channel Comparison & Campaign Performance")
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                # Always show bar chart, if "All Channels", it compares them. If one channel, shows that channel.
                ch_comp = gov_comm.groupby('channel').agg({'delivered_count':'sum', 'clicks':'sum'}).reset_index()
                ch_comp['Rate (%)'] = (ch_comp['clicks'] / ch_comp['delivered_count'] * 100).fillna(0)
                
                fig_bar = px.bar(
                    ch_comp, x='channel', y='Rate (%)', color='channel',
                    hover_data={'delivered_count':':,.0f', 'clicks':':,.0f', 'Rate (%)':':.2f%'},
                    labels={'delivered_count':'Delivered', 'clicks':'Clicks'},
                    title="Channel Efficiency (Delivered-to-Click Rate)"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with v_col2:
                # Campaign Performance Matrix (as requested in dict)
                camp_matrix = gov_comm.groupby(['push_title', 'channel']).agg({'delivered_count':'sum', 'clicks':'sum'}).reset_index()
                camp_matrix['Rate (%)'] = (camp_matrix['clicks'] / camp_matrix['delivered_count'] * 100).fillna(0)
                st.markdown("**Campaign Performance Matrix**")
                st.dataframe(
                    camp_matrix.sort_values('delivered_count', ascending=False).rename(columns={'push_title':'Campaign', 'delivered_count':'Delivered'}), 
                    use_container_width=True, hide_index=True
                )

            # Trend chart (always visible)
            trend_df = gov_comm.groupby(['date', 'channel']).agg({'delivered_count':'sum', 'clicks':'sum'}).reset_index()
            fig_trend = px.line(trend_df, x='date', y='delivered_count', color='channel', title="Performance Over Time (Delivered Volume)", markers=True)
            st.plotly_chart(fig_trend, use_container_width=True)

            # --- 4. Channel-Specific Funnel & Analytics ---
            st.markdown("---")
            st.markdown(f"##### 4. {comm_channel if comm_channel != 'All Channels' else 'Cross-Channel'} Engagement Funnel")
            fc1, fc2 = st.columns([1, 2])
            
            with fc1:
                if comm_channel == 'Email':
                    dels, opens, clicks = gov_comm['delivered_count'].sum(), gov_comm['opens'].sum(), gov_comm['clicks'].sum()
                    st.metric("1. Email Delivered", f"{dels:,.0f}"); st.metric("2. Open Rate", f"{(opens/dels*100):.2f}%" if dels else "0%")
                    st.metric("3. Email Click Rate", f"{(clicks/dels*100):.2f}%" if dels else "0%"); st.metric("4. Click-to-Open Rate", f"{(clicks/opens*100):.2f}%" if opens else "0%")
                    funnel_y, funnel_x = ['Delivered', 'Opened', 'Clicked'], [dels, opens, clicks]
                elif comm_channel == 'Push':
                    dels, shows, clicks = gov_comm['delivered_count'].sum(), gov_comm['sends'].sum(), gov_comm['clicks'].sum()
                    st.metric("1. Push Arrived", f"{dels:,.0f}"); st.metric("2. Show Rate", f"{(shows/dels*100):.2f}%" if dels else "0%")
                    st.metric("3. Push Click Rate", f"{(clicks/dels*100):.2f}%" if dels else "0%"); st.metric("4. Click-to-Show Rate", f"{(clicks/shows*100):.2f}%" if shows else "0%")
                    funnel_y, funnel_x = ['Arrived', 'Shown', 'Clicked'], [dels, shows, clicks]
                elif comm_channel == 'SMS':
                    reqs, dels, elig, clicks = gov_comm['request_count'].sum() if 'request_count' in gov_comm else 0, gov_comm['delivered_count'].sum(), gov_comm['link_eligible_count'].sum() if 'link_eligible_count' in gov_comm else 0, gov_comm['clicks'].sum()
                    st.metric("1. SMS Requested", f"{reqs:,.0f}"); st.metric("2. Delivery Rate", f"{(dels/reqs*100):.2f}%" if reqs else "0%")
                    st.metric("3. Link-enabled SMS", f"{elig:,.0f}"); st.metric("4. SMS Link Click Rate", f"{(clicks/elig*100):.2f}%" if elig else "0%")
                    funnel_y, funnel_x = ['Requested', 'Delivered', 'Link-enabled', 'Clicked'], [reqs, dels, elig, clicks]
                else:
                    # Blended funnel for "All Channels"
                    dels, interacts, clicks = gov_comm['delivered_count'].sum(), gov_comm['opens'].sum(), gov_comm['clicks'].sum()
                    st.metric("1. Total Delivered", f"{dels:,.0f}"); st.metric("2. Interaction Rate", f"{(interacts/dels*100):.2f}%" if dels else "0%")
                    st.metric("3. Overall Click Rate", f"{(clicks/dels*100):.2f}%" if dels else "0%"); st.metric("4. Click-to-Interact Rate", f"{(clicks/interacts*100):.2f}%" if interacts else "0%")
                    funnel_y, funnel_x = ['Delivered (All)', 'Interacted (Opened/Shown)', 'Clicked'], [dels, interacts, clicks]
            
            with fc2:
                fig_funnel = go.Figure(go.Funnel(y=funnel_y, x=funnel_x, marker={"color": ["#4C72B0", "#55A868", "#C44E52", "#8172B3"]}))
                st.plotly_chart(fig_funnel, use_container_width=True)

            # --- 5. Push Time Analysis (Always visible if Push is involved) ---
            if comm_channel in ['Push', 'All Channels']:
                push_data = gov_comm[gov_comm['channel'] == 'Push'] if comm_channel == 'All Channels' else gov_comm
                if not push_data.empty:
                    st.markdown("---")
                    st.markdown("##### 5. Push Time Analysis")
                    st.markdown("*Answering: At what times is Push engagement strongest? (Using Volume & SUM/SUM Rate together)*")
                    tc1, tc2 = st.columns(2)
                    with tc1:
                        # Performance by Hour of Day
                        hr_df = push_data.groupby('hour_of_day').agg({'sends':'sum', 'clicks':'sum'}).reset_index()
                        hr_df['Click-to-Show (%)'] = (hr_df['clicks'] / hr_df['sends'] * 100).fillna(0)
                        fig_hr = go.Figure()
                        fig_hr.add_trace(go.Bar(x=hr_df['hour_of_day'], y=hr_df['sends'], name='Push Shows', marker_color='#4C72B0'))
                        fig_hr.add_trace(go.Scatter(x=hr_df['hour_of_day'], y=hr_df['Click-to-Show (%)'], name='Rate %', yaxis='y2', mode='lines+markers', marker_color='#C44E52'))
                        fig_hr.update_layout(title="Performance by Hour of Day", yaxis=dict(title='Shows Volume'), yaxis2=dict(title='Rate %', overlaying='y', side='right'))
                        st.plotly_chart(fig_hr, use_container_width=True)
                    with tc2:
                        # Day x Hour Heatmap (Volume)
                        heat_df = push_data.pivot_table(index='day_of_week', columns='hour_of_day', values='sends', aggfunc='sum').fillna(0)
                        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        heat_df = heat_df.reindex([d for d in days_order if d in heat_df.index])
                        st.plotly_chart(px.imshow(heat_df, aspect="auto", color_continuous_scale='Blues', title="Push Shows Heatmap (Day × Hour)"), use_container_width=True)

            # --- Raw Data Table ---
            st.markdown("---")
            st.markdown("**📋 Communications Raw Data (Actionable View)**")
            st.dataframe(
                gov_comm[['date', 'channel', 'push_title', 'step_id', 'target_markets', 'sends', 'clicks']],
                column_config={"date": st.column_config.DatetimeColumn("Report Date", format="YYYY-MM-DD"), "push_title": "Campaign Name", "target_markets": "Target Markets"},
                use_container_width=True, hide_index=True
            )
        else:
            st.warning("No communication data matches the current global filters.")
