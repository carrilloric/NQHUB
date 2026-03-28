/**
 * Equity Curve Component
 *
 * D3.js-based equity curve with drawdown overlay
 */

import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp } from 'lucide-react';

interface EquityDataPoint {
  time: Date | string;
  equity: number;
  drawdown?: number;
}

interface EquityCurveProps {
  data: EquityDataPoint[];
  drawdown?: number[];
}

export default function EquityCurve({ data = [], drawdown = [] }: EquityCurveProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    // Generate mock data if no real data
    const mockData: EquityDataPoint[] = data.length > 0 ? data : Array.from({ length: 30 }, (_, i) => {
      const baseValue = 25000;
      const trend = i * 20;
      const noise = Math.sin(i * 0.5) * 200 + Math.random() * 100 - 50;
      const equity = baseValue + trend + noise;

      return {
        time: new Date(Date.now() - (29 - i) * 60 * 60 * 1000), // Last 30 hours
        equity: equity,
        drawdown: Math.max(0, baseValue + i * 30 - equity)
      };
    });

    // Clear previous chart
    d3.select(svgRef.current).selectAll('*').remove();

    // Set dimensions
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const width = containerRef.current.clientWidth - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Parse dates
    const parseData = mockData.map(d => ({
      ...d,
      time: d.time instanceof Date ? d.time : new Date(d.time)
    }));

    // Set scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(parseData, d => d.time) as [Date, Date])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([
        d3.min(parseData, d => d.equity - (d.drawdown || 0))! * 0.99,
        d3.max(parseData, d => d.equity)! * 1.01
      ])
      .range([height, 0]);

    // Create line generator
    const line = d3.line<EquityDataPoint>()
      .x(d => xScale(d.time as Date))
      .y(d => yScale(d.equity))
      .curve(d3.curveMonotoneX);

    // Create area generator for drawdown
    const area = d3.area<EquityDataPoint>()
      .x(d => xScale(d.time as Date))
      .y0(d => yScale(d.equity))
      .y1(d => yScale(d.equity - (d.drawdown || 0)))
      .curve(d3.curveMonotoneX);

    // Add gradient for drawdown
    const gradient = svg.append('defs')
      .append('linearGradient')
      .attr('id', 'drawdownGradient')
      .attr('gradientUnits', 'userSpaceOnUse')
      .attr('x1', 0).attr('y1', yScale(0))
      .attr('x2', 0).attr('y2', yScale(1));

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', 'red')
      .attr('stop-opacity', 0.3);

    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', 'red')
      .attr('stop-opacity', 0.1);

    // Add drawdown area
    g.append('path')
      .datum(parseData)
      .attr('fill', 'url(#drawdownGradient)')
      .attr('d', area);

    // Add X axis
    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickFormat(d3.timeFormat('%H:%M'))
        .ticks(6));

    // Add Y axis
    g.append('g')
      .call(d3.axisLeft(yScale)
        .tickFormat(d => `$${(d as number / 1000).toFixed(1)}k`));

    // Add the equity line
    g.append('path')
      .datum(parseData)
      .attr('fill', 'none')
      .attr('stroke', '#10b981')
      .attr('stroke-width', 2)
      .attr('d', line);

    // Add dots for data points
    g.selectAll('.dot')
      .data(parseData)
      .enter().append('circle')
      .attr('class', 'dot')
      .attr('cx', d => xScale(d.time as Date))
      .attr('cy', d => yScale(d.equity))
      .attr('r', 3)
      .attr('fill', '#10b981');

    // Add tooltip
    const tooltip = d3.select('body').append('div')
      .attr('class', 'tooltip')
      .style('opacity', 0)
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none');

    // Add hover effects
    g.selectAll('.dot')
      .on('mouseover', function(event, d: any) {
        tooltip.transition()
          .duration(200)
          .style('opacity', 0.9);
        tooltip.html(`
          <div>Time: ${d3.timeFormat('%H:%M')(d.time)}</div>
          <div>Equity: $${d.equity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          ${d.drawdown ? `<div>Drawdown: $${d.drawdown.toFixed(2)}</div>` : ''}
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 28) + 'px');
      })
      .on('mouseout', function() {
        tooltip.transition()
          .duration(500)
          .style('opacity', 0);
      });

    // Cleanup
    return () => {
      d3.select('body').selectAll('.tooltip').remove();
    };
  }, [data, drawdown]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Equity Curve
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div ref={containerRef} className="w-full">
          <svg ref={svgRef}></svg>
        </div>
      </CardContent>
    </Card>
  );
}