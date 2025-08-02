import React, { useState, useRef } from 'react';
import { parse } from 'txml';

export default function XMLViewer({ xml, maxLines = Infinity, theme = {}, indentSize = 4 }) {
  const tree = parse(xml);

  const [expandedMap, setExpandedMap] = useState({});
  const toggle = (path) => setExpandedMap(m => ({ ...m, [path]: !m[path] }));

  const lineRef = useRef(1);
  lineRef.current = 1;

  const defaultTheme = {
    container: 'bg-gray-50 p-2 font-mono text-sm overflow-auto',
    lineNumber: 'w-8 inline-block text-gray-400 select-none',
    tagBracket: 'text-blue-500',
    tagName: 'text-purple-600',
    attrName: 'text-yellow-500',
    attrValue: 'text-green-500',
    textNode: 'text-gray-700',
    collapseButton: 'mr-1 select-none cursor-pointer'
  };
  const cls = { ...defaultTheme, ...theme };

  const lines = [];
  function renderNode(node, path, depth) {
    const paddingStyle = { paddingLeft: `${depth * indentSize}ch` };
    const children = node.children || [];
    const elementChildren = children.filter(c => typeof c === 'object');
    const textChildren = children.filter(c => typeof c === 'string' && c.trim());
    const hasKids = elementChildren.length > 0;
    const isExpanded = expandedMap[path] !== false;
    const tagName = node.tagName;

    // Collapsed
    if (hasKids && !isExpanded) {
      lines.push(
        <div key={`${path}-collapsed-inline`} className="flex whitespace-pre">
          <span className={cls.lineNumber}>{lineRef.current++}</span>
          <div style={paddingStyle} className="flex">
            <span onClick={() => toggle(path)} className={cls.collapseButton}>▶</span>
            <span className={cls.tagBracket}>&lt;</span>
            <span className={cls.tagName}>{tagName}</span>
            {Object.entries(node.attributes || {}).map(([name, value], i) => (
              <React.Fragment key={`${path}-attr-${i}`}>
                &nbsp;
                <span className={cls.attrName}>{name}</span>=
                <span className={cls.attrValue}>&quot;{value}&quot;</span>
              </React.Fragment>
            ))}
            <span className={cls.tagBracket}>&gt;</span>
            <span className="text-gray-400 select-none"> {children.length} child nodes </span>
            <span className={cls.tagBracket}>&lt;/</span>
            <span className={cls.tagName}>{tagName}</span>
            <span className={cls.tagBracket}>&gt;</span>
          </div>
        </div>
      );
      return;
    }

    // Opening tag & leaf node
    lines.push(
      <div key={`${path}-open`} className="flex whitespace-pre">
        <span className={cls.lineNumber}>{lineRef.current++}</span>
        <div style={paddingStyle} className="flex">
          {hasKids && (
            <span onClick={() => toggle(path)} className={cls.collapseButton}>
              {isExpanded ? '▼' : '▶'}
            </span>
          )}
          <span className={cls.tagBracket}>&lt;</span>
          <span className={cls.tagName}>{tagName}</span>
          {Object.entries(node.attributes || {}).map(([name, value], i) => (
            <React.Fragment key={`${path}-attr-${i}`}>
              &nbsp;
              <span className={cls.attrName}>{name}</span>=
              <span className={cls.attrValue}>&quot;{value}&quot;</span>
            </React.Fragment>
          ))}
          <span className={cls.tagBracket}>{!hasKids && ' /'}&gt;</span>
        </div>
      </div>
    );

    // Children when expanded
    if (hasKids && isExpanded) {
      elementChildren.forEach((child, idx) => renderNode(child, `${path}-${idx}`, depth + 1));
      textChildren.forEach((txt, j) => {
        lines.push(
          <div key={`${path}-text-${j}`} className="flex whitespace-pre">
            <span className={cls.lineNumber}>{lineRef.current++}</span>
            <div style={paddingStyle}>
              <span className={cls.textNode}>{txt.trim()}</span>
            </div>
          </div>
        );
      });

      // Closing tag
      lines.push(
        <div key={`${path}-close`} className="flex whitespace-pre">
          <span className={cls.lineNumber}>{lineRef.current++}</span>
          <div style={paddingStyle}>
            <span className={cls.tagBracket}>&lt;/</span>
            <span className={cls.tagName}>{tagName}</span>
            <span className={cls.tagBracket}>&gt;</span>
          </div>
        </div>
      );
    } else if (!hasKids && textChildren.length) {
      // Leaf text nodes
      textChildren.forEach((txt, j) => {
        lines.push(
          <div key={`${path}-text-${j}`} className="flex whitespace-pre">
            <span className={cls.lineNumber}>{lineRef.current++}</span>
            <div style={paddingStyle}>
              <span className={cls.textNode}>{txt.trim()}</span>
            </div>
          </div>
        );
      });
    }
  }

  tree.forEach((node, idx) => renderNode(node, `${idx}`, 0));

  const totalLines = lineRef.current - 1;
  const displayed = totalLines > maxLines ? lines.slice(0, maxLines) : lines;

  return (
    <div className={`${cls.container}`}>{displayed}
      {totalLines > maxLines && (
        <div className="mt-1 text-center text-gray-500 select-none">
          ... {totalLines - maxLines} lines hidden ...
        </div>
      )}
    </div>
  );
}
