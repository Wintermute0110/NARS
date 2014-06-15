<?xml version='1.0'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <!-- Debian -->
  <xsl:import href="/usr/share/xml/docbook/stylesheet/docbook-xsl/xhtml/onechunk.xsl"/>
  <!-- Cygwin -->
  <!-- <xsl:import href="/usr/share/sgml/docbook/xsl-stylesheets/xhtml/onechunk.xsl"/> -->

  <xsl:param name="chunker.output.encoding">UTF-8</xsl:param>
  <xsl:param name="toc.max.depth">4</xsl:param>
  <xsl:param name="html.stylesheet" select="'default.css'"/>
  <xsl:param name="admon.graphics">0</xsl:param>

  <!-- Customize output filename -->
  <!-- http://www.sagehill.net/docbookxsl/OneChunk.html -->
  <xsl:param name="root.filename"></xsl:param>
  <xsl:param name="use.id.as.filename">1</xsl:param>
</xsl:stylesheet>
