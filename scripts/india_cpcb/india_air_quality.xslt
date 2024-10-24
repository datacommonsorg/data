<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output indent="yes"/>
    <xsl:strip-space elements="*"/>
    <xsl:template match="Station">
        <Station>
            <SiteName><xsl:value-of select="@id"/></SiteName>
            <City><xsl:value-of select="../@id"/></City>
            <State><xsl:value-of select="../../@id"/></State>
            <Country><xsl:value-of select="../../../@id"/></Country>
            <LastUpdate><xsl:value-of select="@lastupdate"/></LastUpdate>
            <Latitude><xsl:value-of select="@latitude"/></Latitude>
            <Longitude><xsl:value-of select="@longitude"/></Longitude>
            <xsl:apply-templates select="Pollutant_Index"/>
            <AQI><xsl:value-of select="Air_Quality_Index/@Value"/></AQI>
        </Station>
    </xsl:template>

    <xsl:template match="Pollutant_Index">
        <xsl:element name="{@id}_Mean">
            <xsl:value-of select="@Avg"/>
        </xsl:element>
        <xsl:element name="{@id}_Min">
            <xsl:value-of select="@Min"/>
        </xsl:element>
        <xsl:element name="{@id}_Max">
            <xsl:value-of select="@Max"/>
        </xsl:element>
    </xsl:template>
</xsl:stylesheet>