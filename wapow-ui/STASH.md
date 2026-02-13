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
                        'taxonomy.sections._id': ['/style'],
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
        // must_not: [
        //   {
        //     nested: {
        //       path: "taxonomy.sections",
        //       query: {
        //         bool: {
        //           must: [
        //             {
        //               terms: {
        //                 "taxonomy.sections._id": sectionsExcluded
        //               }
        //             },
        //             {
        //               term: {
        //                 "taxonomy.sections._website": website
        //               }
        //             }
        //           ]
        //         }
        //       }
        //     }
        //   }
        // ]
      },
    },
  }


    // return `/content/v4/search/published?body=${encodedBody}&website=${website}&size=${feedSize}&from=${feedOffset}&sort=display_date:desc`;



export interface Article {
  _id: string
  additional_properties: {
    ai_summary: string | null
    apple_news: {
      exclude_apple_news: boolean
      is_developing: boolean
    }
    audio_article: {
      automated: {
        generate: boolean
        manifest_url: string
        voices: string[]
      }
      enabled: boolean
      type: string
    }
    audio_article_ads_url: string
    audio_article_enabled: boolean
    audio_article_raw_url: string
    clipboard: Record<string, any>
    first_display_date: string
    has_published_copy: boolean
    isNewsServiceCloneCreated: boolean
    is_published: boolean
    news_service: {
      attention_line: string
      categories: Record<string, string[]>
      category: string
      clone_to_news_service: boolean
      correction: boolean
      nss_site_correction: boolean
      print_only: boolean
      release_date: string
      staff_writer: boolean
      writers_group: boolean
    }
    page_title: string
    parse_errors: any[]
    poll_frequency: number
    present_display_date: string
    present_publish_date: string
    pubble_app_id: string
    publish_date: boolean | string
    publish_embargo: string
    publish_embargo_indefinitely: boolean
    seo_canonical_url: string
    time_to_listen: string
    time_to_read: string
    topic_description: string
    tracking: {
      commercial_node: string
    }
    truncate_posts: boolean
  }
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
          books: any[]
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
  planning: {
    budget_line: string
    scheduling: {
      planned_publish_date: string
    }
    story_length: {
      inch_count_actual: number
      line_count_actual: number
      word_count_actual: number
    }
  }
  publish_date: string
  publishing: {
    scheduled_operations: {
      publish_edition: any[]
      unpublish_edition: any[]
    }
  }
  related_content: {
    basic: Array<{
      _id: string
      additional_properties: Record<string, any>
      address: Record<string, any>
      canonical_url: string
      canonical_website: string
      comments: {
        allow_comments: boolean
        display_comments: boolean
        moderation_required: boolean
      }
      content_elements: Array<{
        _id: string
        additional_properties: Record<string, any>
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
          additional_properties: Record<string, any>
          referent: {
            id: string
            provider: string
            referent_properties: Record<string, any>
            type: string
          }
          type: string
        }>
      }
      description: {
        basic: string
        expanded_byline: string
      }
      display_date: string
      distributor: {
        category: string
        name: string
        subcategory: string
      }
      first_publish_date: string
      headlines: {
        apple_news: string
        basic: string
        meta_title: string
        mobile: string
        native: string
        print: string
        tablet: string
        web: string
      }
      label: {
        transparency: {
          display: boolean
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
      planning: {
        budget_line: string
        story_length: {
          inch_count_actual: number
          line_count_actual: number
          word_count_actual: number
        }
      }
      publish_date: string
      related_content: {
        basic: any[]
        clonedChildren: any[]
        clonedFromParent: any[]
        redirect: any[]
      }
      revision: {
        branch: string
        editions: any[]
        parent_id: string
        revision_id: string
        user_id: string
      }
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
        additional_properties: {
          parent_site_primaries: any[]
        }
        primary_section: {
          additional_properties: Record<string, any>
          referent: {
            id: string
            provider: string
            type: string
            website: string
          }
          type: string
        }
        primary_site: {
          additional_properties: Record<string, any>
          referent: {
            id: string
            provider: string
            type: string
          }
          type: string
        }
        sections: Array<{
          additional_properties: Record<string, any>
          referent: {
            id: string
            provider: string
            type: string
            website: string
          }
          type: string
        }>
        seo_keywords: any[]
        sites: Array<{
          additional_properties: Record<string, any>
          referent: {
            id: string
            provider: string
            type: string
          }
          type: string
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
      websites: {
        washpost: {
          website_section: {
            additional_properties: Record<string, any>
            referent: {
              id: string
              type: string
              website: string
            }
            type: string
          }
          website_url: string
        }
      }
      workflow: {
        status_code: number
      }
    }>
    clonedChildren: any[]
    clonedFromParent: Array<{
      referent: {
        id: string
      }
      type: string
    }>
    redirect: any[]
  }
  revision: {
    branch: string
    editions: string[]
    parent_id: string
    published: boolean
    revision_id: string
    user_id: string
  }
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
  tracking: {
    author_desk: string
    author_id: string
    author_name: string
    author_subdesk: string
    author_type: string
    content_topics: string
  }
  type: string
  version: string
  website: string
  website_url: string
  websites: {
    washpost: {
      website_section: {
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
      }
      website_url: string
    }
  }
  workflow: {
    status_code: number
  }
}
