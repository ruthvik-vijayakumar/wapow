import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Washington Post Article Interface based on new JSON structure
export interface Article {
  _id: string
  ai_summary: any,
  additional_properties: any
  canonical_url: string
  canonical_website: string
  comments: {
    ai_prompt: {
      content: string
      display_avatar: boolean
      enabled: boolean
    }
    ai_summary: {
      enabled: boolean
    }
    display_comments: boolean
  }
  content_elements: Array<{
    _id: string
    additional_properties: {
      _id: number
      cadit_quaestio: any[]
    }
    content: string
    type: string
  }>
  content_restrictions: {
    content_code: string
  }
  copyright: string
  created_date: string
  credits: {
    audio_narrators: any[]
    audio_producers: any[]
    by: Array<{
      _id: string
      additional_properties: {
        original: {
          _id: string
          affiliations: string
          author_type: string
          awards: any[]
          beat: string
          bio: string
          bio_page: string
          byline: string
          contributor: boolean
          custom_washpost_desk_name_1: string
          custom_washpost_desk_name_2: string
          education: Array<{
            name: string
          }>
          email: string
          employeeID: string
          expertise: string
          firstName: string
          fuzzy_match: boolean
          image: string
          isWorkdayLoad: boolean
          jobProfile: string
          lastName: string
          last_updated_date: string
          location: string
          longBio: string
          middleName: string
          native_app_rendering: boolean
          networkID: string
          newsDesk: string
          newsJobCategory: string
          personal_website: string
          podcasts: any[]
          role: string
          secondLastName: string
          slug: string
          status: string
          subDesk: string
          subDeskHead: string
          twitter: string
          workerType: string
        }
      }
  description: string
      image: {
        url: string
        version: string
      }
    name: string
      org: string
      slug: string
      socialLinks: Array<{
        deprecated: boolean
        deprecation_msg: string
        site: string
        url: string
      }>
      social_links: Array<{
        site: string
        url: string
      }>
      type: string
      url: string
      version: string
    }>
  }
  description: {
    basic: string
    expanded_byline: string
  }
  display_date: string
  first_publish_date: string
  headlines: {
    apple_news: string
    basic: string
    meta_title: string
    mobile: string
    native: string
    print: string
    tablet: string
    url: string
    web: string
  }
  label: {
    basic: {
      display: boolean
      text: string
      url: string
    }
    transparency: {
      display: boolean
      text: string
      url: string
    }
  }
  label_display: {
    basic: {
      text: string
      url: string
    }
    transparency: {
      text: string
      url: string
    }
  }
  language: string
  last_updated_date: string
  location: string
  owner: {
  id: string
    name: string
  }
  promo_items?: {
    basic: {
      additional_properties: {
        categoryFilter: string
        editors_pick: boolean
        file_size: number
        fullSizeResizeUrl: string
        galleries: any[]
        image_type: string
        mime_type: string
        originalName: string
        originalUrl: string
        proxyUrl: string
        published: boolean
        resizeUrl: string
        restricted: boolean
        thumbnailUrl: string
        version: string
      }
      address: {
        locality: string
        region: string
      }
      caption: string
      caption_display: string
      copyright: string
      created_date: string
      credits: {
        affiliation: any[]
        by: any[]
      }
      credits_caption_display: string
      credits_display: string
      height: number
      last_updated_date: string
      licensable: boolean
      owner: {
  id: string
      }
      related_content: {
        derivative_of: any[]
      }
      source: {
        edit_url: string
        system: string
      }
      status: string
      subtitle: string
      subtype: string
      taxonomy: Record<string, any>
      type: string
      url: string
      version: string
      width: number
      _id: string
    }
  }
  planning?: {
    budget_line: string
    scheduling?: {
      planned_publish_date: string
    }
    story_length?: {
      inch_count_actual: number
      line_count_actual: number
      word_count_actual: number
    }
  }
  publishing?: {
    audience: string
    publish_date: string
    publish_time: string
    timezone: string
  }
  related_content?: {
    basic: any[]
    clonedChildren?: any[]
    clonedFromParent?: any[]
    redirect?: any[]
  }
  revision?: {
    published: boolean
    branch?: string
    editions?: any[]
    parent_id?: string
    revision_id?: string
    user_id?: string
  }
  tracking?: {
    inURL: string
    storyID: string
    author_desk?: string
    author_id?: string
    author_name?: string
    author_subdesk?: string
    author_type?: string
    content_topics?: string
  }
  websites?: Record<string, any>
  workflow?: {
    status_code: number
  }
  publish_date: string
  slug: string
  source: {
    name: string
    source_type: string
    system: string
  }
  subheadlines: {
    basic: string
  }
  subtype: string
  syndication: {
    external_distribution: boolean
    follow: boolean
    search: boolean
  }
  taxonomy: {
    primary_section: {
      _id: string
      _website: string
      additional_properties: {
        original: {
          _admin: {
            alias_ids: string[]
            commercial_node: string
            default_content: string
            tracking_node: string
          }
          _id: string
          _website: string
          ancestors: Record<string, string[]>
          inactive: boolean
          most_read: {
            most_read_display_name: string
            most_read_feed_section: string
            most_read_link_url: string
          }
          name: string
          navigation: {
            nav_title: string
          }
          node_type: string
          order: Record<string, number>
          parent: Record<string, string>
          site: {
            generate_spectrum_jsonapp: string
            meta_title: string
            path_fusion: string
            site_about: string | null
            site_description: string
            site_keywords: string | null
            site_tagline: string | null
            site_title: string
            site_url: string
            site_url_section: string
            tracking_page_name: string
            tracking_section: string
            tracking_subsection: string
          }
          site_topper: {
            hide_parent_section_breadcrumb: string
            parent_section_breadcrumb_override: string | null
            secondary_nav_alternate_section_to_use: string
            secondary_nav_instead_of_custom_links: string
          }
          social: {
            facebook: string | null
            rss: string | null
            twitter: string | null
          }
          story_list: {
            story_list_content: Record<string, any>
          }
          syndication: {
            apple_news_sections: string[]
            paywall: string
          }
        }
      }
  description: string
    name: string
      parent: {
        default: string
      }
      parent_id: string
      path: string
      type: string
      version: string
    }
    primary_site: {
      _id: string
      additional_properties: {
        original: {
          _admin: {
            alias_ids: string[]
            commercial_node: string
            default_content: string
            tracking_node: string
          }
          _id: string
          ancestors: string[]
          inactive: boolean
          most_read: {
            most_read_display_name: string
            most_read_feed_section: string
            most_read_link_url: string
          }
          name: string
          navigation: {
            nav_title: string
          }
          parent: string
          site: {
            generate_spectrum_jsonapp: string
            meta_title: string
            path_fusion: string
            site_about: string | null
            site_description: string
            site_keywords: string | null
            site_tagline: string | null
            site_title: string
            site_url: string
            site_url_section: string
            social_share_image: string
            tracking_page_name: string
            tracking_section: string
            tracking_subsection: string
          }
          site_topper: {
            hide_parent_section_breadcrumb: string
            parent_section_breadcrumb_override: string | null
            secondary_nav_alternate_section_to_use: string
          }
          social: {
            archive_start_date: string
            archives: string
            facebook: string | null
            rss: string
            twitter: string | null
          }
          story_list: {
            story_list_content: Record<string, any>
          }
          syndication: {
            apple_news_sections: string[]
            paywall: string
          }
        }
      }
      description: string
      name: string
      parent_id: string
      path: string
      type: string
      version: string
    }
    sections: Array<{
      _id: string
      _website: string
      _website_section_id: string
      additional_properties: {
        original: {
          _admin: {
            alias_ids: string[]
            commercial_node: string
            default_content: string
            tracking_node: string
          }
          _id: string
          _website: string
          ancestors: Record<string, string[]>
          inactive: boolean
          most_read: {
            most_read_display_name: string
            most_read_feed_section: string
            most_read_link_url: string
          }
          name: string
          navigation: {
            nav_title: string
          }
          node_type: string
          order: Record<string, number>
          parent: Record<string, string>
          site: {
            generate_spectrum_jsonapp: string
            meta_title: string
            path_fusion: string
            site_about: string | null
            site_description: string
            site_keywords: string | null
            site_tagline: string | null
            site_title: string
            site_url: string
            site_url_section: string
            tracking_page_name: string
            tracking_section: string
            tracking_subsection: string
          }
          site_topper: {
            hide_parent_section_breadcrumb: string
            parent_section_breadcrumb_override: string | null
            secondary_nav_alternate_section_to_use: string
            secondary_nav_instead_of_custom_links: string
          }
          social: {
            facebook: string | null
            rss: string | null
            twitter: string | null
          }
          story_list: {
            story_list_content: Record<string, any>
          }
          syndication: {
            apple_news_sections: string[]
            paywall: string
          }
        }
      }
      description: string
      name: string
      parent: {
        default: string
      }
      parent_id: string
      path: string
      type: string
      version: string
    }>
    seo_keywords: any[]
    sites: Array<{
      _id: string
      additional_properties: {
        original: {
          _admin: {
            alias_ids: string[]
            commercial_node: string
            default_content: string
            tracking_node: string
          }
          _id: string
          custom_cta: {
            cta_active: string
            cta_icon: string
            cta_text: string
            cta_url: string
          }
          inactive: boolean
          most_read: {
            most_read_display_name: string
            most_read_feed_section: string
            most_read_link_url: string
          }
          name: string
          navigation: {
            nav_title: string
          }
          parent: string
          site: {
            meta_title: string
            path_fusion: string
            site_about: string | null
            site_description: string
            site_keywords: string | null
            site_tagline: string | null
            site_title: string
            site_url: string
            site_url_section: string
            social_share_image: string
            tracking_page_name: string
            tracking_section: string
            tracking_subsection: string
          }
          site_topper: {
            hide_parent_section_breadcrumb: string
            parent_section_breadcrumb_override: string | null
            secondary_nav_alternate_section_to_use: string
          }
          social: {
            archive_start_date: string
            archives: string
            facebook: string | null
            rss: string
            twitter: string | null
          }
          story_list: {
            story_list_content: Record<string, any>
          }
          syndication: {
            apple_news_sections: string[]
            paywall: string
          }
        }
      }
      description: string
      name: string
      parent_id: string
      path: string
      type: string
      version: string
    }>
    taggings: {
      basic: {
        additional_properties: {
          topics_author: string
          topics_date: string
        }
        auxiliaries: Array<{
          _id: string
          name: string
          score: number
          uid: string
        }>
        topics: Array<{
          _id: string
          name: string
          score: number
          uid: string
        }>
      }
    }
    tags: Array<{
      additional_properties?: Record<string, any>
      description: string
      slug: string
      text: string
    }>
  }
  type: string
  version: string
  website: string
  website_url: string
}

// New interfaces for different media types
export interface Video {
  aspect_ratio: number
  content_id: string
  canonical_url: string
  promo_image: {
    url: string
  }
  streams: Array<{
    bitrate: number
    filesize: number
    height: number
    provider: string
    stream_type: string
    url: string
    width: number
  }>
  duration: number
  tracking: {
    page_name: string
    video_category: string
    video_section: string
    video_source: string
    page_title: string
    av_name: string
    av_arc_id: string
  }
}

export interface StoryContent {
  id: string
  title: string
  description: string
  thumbnail: string
  author: {
    name: string
    avatar: string
    username: string
  }
  likes: number
  comments: number
  shares: number
  views: number
  duration: string
  createdAt: string
  aspectRatio: number
  mediaType: 'story'
}

export type MediaItem =  Video | StoryContent

export const useContentStore = defineStore('content', () => {

  const videos = ref<Video[]>([])
  const podcastClips = ref<StoryContent[]>([])
  const articles = ref<Article[]>([])
  const currentVideoIndex = ref(0)
  const isLoading = ref(false)

  const createArticleFromSource = (source: any): Article => {
    return {
      _id: source._id || source.content_id || "",
      ai_summary: source.ai_summary || {},
      additional_properties: source.additional_properties || {},
      canonical_url: source.canonical_url || "",
      canonical_website: source.canonical_website || "washpost",
      comments: {
        ai_prompt: {
          content: source.comments?.ai_prompt?.content || "",
          display_avatar: source.comments?.ai_prompt?.display_avatar || false,
          enabled: source.comments?.ai_prompt?.enabled || false,
        },
        ai_summary: {
          enabled: source.comments?.ai_summary?.enabled || false,
        },
        display_comments: source.comments?.display_comments || false,
      },
      content_elements: source.content_elements || [],
      content_restrictions: {
        content_code: source.content_restrictions?.content_code || "default",
      },
      copyright: source.copyright || "The Washington Post",
      created_date: source.created_date || "",
      credits: {
        audio_narrators: source.credits?.audio_narrators || [],
        audio_producers: source.credits?.audio_producers || [],
        by: source.credits?.by || [],
      },
      description: {
        basic: source.description?.basic || "",
        expanded_byline: source.description?.expanded_byline || "",
      },
      display_date: source.display_date || "",
      first_publish_date: source.first_publish_date || "",
      headlines: {
        apple_news: source.headlines?.apple_news || "",
        basic: source.headlines?.basic || "",
        meta_title: source.headlines?.meta_title || "",
        mobile: source.headlines?.mobile || "",
        native: source.headlines?.native || "",
        print: source.headlines?.print || "",
        tablet: source.headlines?.tablet || "",
        url: source.headlines?.url || "",
        web: source.headlines?.web || "",
      },
      label: {
        basic: {
          display: source.label?.basic?.display || false,
          text: source.label?.basic?.text || "",
          url: source.label?.basic?.url || "",
        },
        transparency: {
          display: source.label?.transparency?.display || false,
          text: source.label?.transparency?.text || "",
          url: source.label?.transparency?.url || "",
        },
      },
      label_display: {
        basic: {
          text: source.label_display?.basic?.text || "",
          url: source.label_display?.basic?.url || "",
        },
        transparency: {
          text: source.label_display?.transparency?.text || "",
          url: source.label_display?.transparency?.url || "",
        },
      },
      language: source.language || "en",
      last_updated_date: source.last_updated_date || "",
      location: source.location || "",
      owner: {
        id: source.owner?.id || "washpost",
        name: source.owner?.name || "The Washington Post",
      },
      promo_items: source.promo_items ? {
        basic: {
          additional_properties: {
            categoryFilter: source.promo_items.basic?.additional_properties?.categoryFilter || "",
            editors_pick: source.promo_items.basic?.additional_properties?.editors_pick || false,
            file_size: source.promo_items.basic?.additional_properties?.file_size || 0,
            fullSizeResizeUrl: source.promo_items.basic?.additional_properties?.fullSizeResizeUrl || "",
            galleries: source.promo_items.basic?.additional_properties?.galleries || [],
            image_type: source.promo_items.basic?.additional_properties?.image_type || "",
            mime_type: source.promo_items.basic?.additional_properties?.mime_type || "",
            originalName: source.promo_items.basic?.additional_properties?.originalName || "",
            originalUrl: source.promo_items.basic?.additional_properties?.originalUrl || "",
            proxyUrl: source.promo_items.basic?.additional_properties?.proxyUrl || "",
            published: source.promo_items.basic?.additional_properties?.published || false,
            resizeUrl: source.promo_items.basic?.additional_properties?.resizeUrl || "",
            restricted: source.promo_items.basic?.additional_properties?.restricted || false,
            thumbnailUrl: source.promo_items.basic?.additional_properties?.thumbnailUrl || "",
            version: source.promo_items.basic?.additional_properties?.version || "",
          },
          address: {
            locality: source.promo_items.basic?.address?.locality || "",
            region: source.promo_items.basic?.address?.region || "",
          },
          caption: source.promo_items.basic?.caption || "",
          caption_display: source.promo_items.basic?.caption_display || "",
          copyright: source.promo_items.basic?.copyright || "",
          created_date: source.promo_items.basic?.created_date || "",
          credits: {
            affiliation: source.promo_items.basic?.credits?.affiliation || [],
            by: source.promo_items.basic?.credits?.by || [],
          },
          credits_caption_display: source.promo_items.basic?.credits_caption_display || "",
          credits_display: source.promo_items.basic?.credits_display || "",
          height: source.promo_items.basic?.height || 0,
          last_updated_date: source.promo_items.basic?.last_updated_date || "",
          licensable: source.promo_items.basic?.licensable || false,
          owner: {
            id: source.promo_items.basic?.owner?.id || "",
          },
          related_content: {
            derivative_of: source.promo_items.basic?.related_content?.derivative_of || [],
          },
          source: {
            edit_url: source.promo_items.basic?.source?.edit_url || "",
            system: source.promo_items.basic?.source?.system || "",
          },
          status: source.promo_items.basic?.status || "",
          subtitle: source.promo_items.basic?.subtitle || "",
          subtype: source.promo_items.basic?.subtype || "",
          taxonomy: source.promo_items.basic?.taxonomy || {},
          type: source.promo_items.basic?.type || "",
          url: source.promo_items.basic?.url || "",
          version: source.promo_items.basic?.version || "",
          width: source.promo_items.basic?.width || 0,
          _id: source.promo_items.basic?._id || "",
        }
      } : undefined,
      planning: source.planning ? {
        budget_line: source.planning?.budget_line || "",
        scheduling: source.planning?.scheduling ? {
          planned_publish_date: source.planning.scheduling?.planned_publish_date || "",
        } : undefined,
        story_length: source.planning?.story_length ? {
          inch_count_actual: source.planning.story_length?.inch_count_actual || 0,
          line_count_actual: source.planning.story_length?.line_count_actual || 0,
          word_count_actual: source.planning.story_length?.word_count_actual || 0,
        } : undefined,
      } : undefined,
      publishing: source.publishing ? {
        audience: source.publishing?.audience || "",
        publish_date: source.publishing?.publish_date || "",
        publish_time: source.publishing?.publish_time || "",
        timezone: source.publishing?.timezone || "",
      } : undefined,
      related_content: source.related_content ? {
        basic: source.related_content?.basic || [],
        clonedChildren: source.related_content?.clonedChildren || [],
        clonedFromParent: source.related_content?.clonedFromParent || [],
        redirect: source.related_content?.redirect || [],
      } : undefined,
      revision: source.revision ? {
        published: source.revision?.published || false,
        branch: source.revision?.branch || "",
        editions: source.revision?.editions || [],
        parent_id: source.revision?.parent_id || "",
        revision_id: source.revision?.revision_id || "",
        user_id: source.revision?.user_id || "",
      } : undefined,
      tracking: source.tracking ? {
        inURL: source.tracking?.inURL || "",
        storyID: source.tracking?.storyID || "",
        author_desk: source.tracking?.author_desk || "",
        author_id: source.tracking?.author_id || "",
        author_name: source.tracking?.author_name || "",
        author_subdesk: source.tracking?.author_subdesk || "",
        author_type: source.tracking?.author_type || "",
        content_topics: source.tracking?.content_topics || "",
      } : undefined,
      websites: source.websites || {},
      workflow: source.workflow ? {
        status_code: source.workflow?.status_code || 5,
      } : undefined,
      publish_date: source.publish_date || "",
      slug: source.slug || "",
      source: {
        name: source.source?.name || "The Washington Post",
        source_type: source.source?.source_type || "staff",
        system: source.source?.system || "washpost",
      },
      subheadlines: {
        basic: source.subheadlines?.basic || "",
      },
      subtype: source.subtype || "story",
      syndication: {
        external_distribution: source.syndication?.external_distribution || false,
        follow: source.syndication?.follow || false,
        search: source.syndication?.search || false,
      },
      taxonomy: source.taxonomy || {
        primary_section: {
          _id: "",
          _website: "washpost",
          additional_properties: {
            original: {
              _admin: {
                alias_ids: [],
                commercial_node: "",
                default_content: "",
                tracking_node: "",
              },
              _id: "",
              _website: "washpost",
              ancestors: {},
              inactive: false,
              most_read: {
                most_read_display_name: "",
                most_read_feed_section: "",
                most_read_link_url: "",
              },
              name: "",
              navigation: {
                nav_title: "",
              },
              node_type: "",
              order: {},
              parent: {},
              site: {
                generate_spectrum_jsonapp: "",
                meta_title: "",
                path_fusion: "",
                site_about: null,
                site_description: "",
                site_keywords: null,
                site_tagline: null,
                site_title: "",
                site_url: "",
                site_url_section: "",
                tracking_page_name: "",
                tracking_section: "",
                tracking_subsection: "",
              },
              site_topper: {
                hide_parent_section_breadcrumb: "",
                parent_section_breadcrumb_override: null,
                secondary_nav_alternate_section_to_use: "",
                secondary_nav_instead_of_custom_links: "",
              },
              social: {
                facebook: null,
                rss: null,
                twitter: null,
              },
              story_list: {
                story_list_content: {},
              },
              syndication: {
                apple_news_sections: [],
                paywall: "",
              },
            },
          },
          description: "",
          name: "",
          parent: {
            default: "",
          },
          parent_id: "",
          path: "",
          type: "",
          version: "",
        },
        primary_site: {
          _id: "",
          additional_properties: {
            original: {
              _admin: {
                alias_ids: [],
                commercial_node: "",
                default_content: "",
                tracking_node: "",
              },
              _id: "",
              ancestors: [],
              inactive: false,
              most_read: {
                most_read_display_name: "",
                most_read_feed_section: "",
                most_read_link_url: "",
              },
              name: "",
              navigation: {
                nav_title: "",
              },
              parent: "",
              site: {
                generate_spectrum_jsonapp: "",
                meta_title: "",
                path_fusion: "",
                site_about: null,
                site_description: "",
                site_keywords: null,
                site_tagline: null,
                site_title: "",
                site_url: "",
                site_url_section: "",
                social_share_image: "",
                tracking_page_name: "",
                tracking_section: "",
                tracking_subsection: "",
              },
              site_topper: {
                hide_parent_section_breadcrumb: "",
                parent_section_breadcrumb_override: null,
                secondary_nav_alternate_section_to_use: "",
              },
              social: {
                archive_start_date: "",
                archives: "",
                facebook: null,
                rss: "",
                twitter: null,
              },
              story_list: {
                story_list_content: {},
              },
              syndication: {
                apple_news_sections: [],
                paywall: "",
              },
            },
          },
          description: "",
          name: "",
          parent_id: "",
          path: "",
          type: "",
          version: "",
        },
        sections: [],
        seo_keywords: [],
        sites: [],
        taggings: {
          basic: {
            additional_properties: {
              topics_author: "",
              topics_date: "",
            },
            auxiliaries: [],
            topics: [],
          },
        },
        tags: [],
      },
      type: source.type || "story",
      version: source.version || "0.10.14",
      website: source.website || "washpost",
      website_url: source.website_url || "",
    }
  }

  const getSectionData = async (category_id: string) => {
    const website = 'washpost'
    const body = {
      query: {
        bool: {
          must: [
            {
              term: {
                'revision.published': 'true',
              },
            },
            {
              nested: {
                path: 'taxonomy.sections',
                query: {
                  bool: {
                    must: [
                      {
                        terms: {
                          'taxonomy.sections._id': [category_id],
                        },
                      },
                      {
                        term: {
                          'taxonomy.sections._website': website,
                        },
                      },
                    ],
                  },
                },
              },
            },
          ],
        },
      },
    }
    //`https://prism.wpit.nile.works/content/v4/search/published?body=${encodedBody}&size=${feedSize}&website=${website}&sort=display_date:desc`
    const encodedBody = encodeURI(JSON.stringify(body))
    const response = await fetch(
              `${import.meta.env.VITE_ARTICLES_API || 'http://localhost:3001'}/api${category_id}`,
      {
        method: 'GET',
      },
    )
    const data = await response.json()
    return data
  }

  // Load articles from JSON data
  const loadArticles = async (apiCategoryId: string) => {
    const {data} = await getSectionData(apiCategoryId)
    const filteredData = data.filter((article: any) => {
      // Skip items with empty canonical_url
      if (!article.canonical_url || article.canonical_url === "") {
        return false
      }
      if (!article.promo_items || Object.keys(article.promo_items).length === 0) {
        return false
      }
      return true
    })

    articles.value = filteredData.map((article: any) => createArticleFromSource(article))
  }

  // Get articles by section
  const getArticlesBySection = (section: string): Article[] => {
    return articles.value.filter(article =>
      article.taxonomy?.primary_section?.name === section ||
      article.taxonomy?.sections?.some(s => s.name === section) ||
      article.type === section
    )
  }

  // Get articles by type
  const getArticlesByType = (type: string): Article[] => {
    return articles.value.filter(article => article.type === type)
  }

  // Get trending articles (most recent)
  const getTrendingArticles = (limit: number = 10): Article[] => {
    return articles.value
      .sort((a, b) => new Date(b.display_date).getTime() - new Date(a.display_date).getTime())
      .slice(0, limit)
  }

  // Convert article to video format for backward compatibility
  const convertArticleToVideo = (article: Article): Video => {
    return {
      aspect_ratio: 16/9,
      content_id: article._id,
      canonical_url: article.canonical_url,
      promo_image: {
        url: article.promo_items?.basic?.url || ''
      },
      streams: [],
      duration: 0,
      tracking: {
        page_name: '',
        video_category: 'vertical',
        video_section: article.taxonomy?.primary_section?.name || '',
        video_source: 'The Washington Post',
        page_title: article.headlines?.basic || '',
        av_name: '',
        av_arc_id: ''
      }
    }
  }

  // Get all articles as videos for backward compatibility
  const getArticlesAsVideos = (): Video[] => {
    return articles.value.map(convertArticleToVideo)
  }

  // Load videos from localStorage on store initialization
  const loadVideos = async () => {
    videos.value = await generateVerticalVideos()
    podcastClips.value = await generatePodcastClips()
  }

  // Generate vertical video data from local videos.json
  const generateVerticalVideos = async (): Promise<Video[]> => {
    try {
      const { data } = await getSectionData('/videos')
      console.log('videos', data)
      console.log('Loaded videos from videos.json:', data?.length || 0, 'videos')

      // Convert the raw video data to the expected Video interface format
      const convertedVideos = data?.map((video: any) => ({
        aspect_ratio: video.aspect_ratio,
        content_id: video.content_id,
        canonical_url: video.canonical_url,
        promo_image: {
          url: video.promo_image?.url || ''
        },
        streams: video.streams || [],
        duration: 0, // We'll need to calculate this from streams if needed
        tracking: {
          page_name: '',
          video_category: 'vertical',
          video_section: '',
          video_source: 'The Washington Post',
          page_title: video.canonical_url.split('/').pop()?.replace('.html', '') || 'Video',
          av_name: '',
          av_arc_id: ''
        }
      })) || []

      console.log('Converted videos:', convertedVideos.length, 'videos')
      console.log('Sample converted video:', convertedVideos[0])

      return convertedVideos
    } catch (error) {
      console.error('Error loading videos from videos.json:', error)
      return []
    }
  }

  // Generate podcast clip data with lyrics
  const generatePodcastClips = async (): Promise<StoryContent[]> => {
      const {data} = await getSectionData('/podcasts')
      console.log('podcastClips', data)
      return data.map((clip: any) => ({
        id: clip._id,
        title: clip.headlines?.basic,
        description: clip.description?.basic,
        audioUrl: clip.additional_properties?.audio_article_raw_url || clip.additional_properties?.audio[0].url,
        thumbnail: clip.promo_items?.basic?.url || clip.additional_properties?.lead_art.url,
        author: { name: 'The Washington Post', username: '@washingtonpost', avatar: 'https://picsum.photos/50/50?random=wapo' }
    }))
  }

  // Computed properties
  const currentVideo = computed(() => videos.value[currentVideoIndex.value])
  const totalVideos = computed(() => videos.value.length)

  // Actions
  const nextVideo = () => {
    if (currentVideoIndex.value < videos.value.length - 1) {
      currentVideoIndex.value++
    }
  }

  const previousVideo = () => {
    if (currentVideoIndex.value > 0) {
      currentVideoIndex.value--
    }
  }

  const goToVideo = (index: number) => {
    if (index >= 0 && index < videos.value.length) {
      currentVideoIndex.value = index
    }
  }


  // Initialize store
  loadVideos()

  // Helper function to get all media items
  const getAllMediaItems = computed((): MediaItem[] => {
    return [
      ...videos.value,
      ...podcastClips.value,
    ]
  })

  // Helper function to get media by type
  const getMediaByType = (type: string) => {
    switch (type) {
      case 'video':
        return videos.value
      case 'podcast':
        return podcastClips.value
      default:
        return getAllMediaItems.value
    }
  }

  return {
    videos,
    podcastClips,
    articles,
    currentVideoIndex,
    isLoading,
    currentVideo,
    totalVideos,
    getAllMediaItems,
    getMediaByType,
    nextVideo,
    previousVideo,
    goToVideo,
    loadArticles,
    getArticlesBySection,
    getArticlesByType,
    getTrendingArticles,
    getArticlesAsVideos,
    convertArticleToVideo,
    loadVideos,
  }
})
